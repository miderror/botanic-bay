# Обработка ошибок в бэкенде

## Общий подход

В приложении реализована многоуровневая система обработки ошибок, которая обеспечивает:
- Согласованность в обработке исключений между слоями
- Структурированное логирование ошибок
- Правильные HTTP-коды ответов для API
- Безопасность (не утечка внутренних деталей в production)

## Архитектура обработки ошибок

### Иерархия слоев (снизу вверх):
1. **CRUD слой** (app/crud/) - работа с БД
2. **Сервисный слой** (app/services/) - бизнес-логика
3. **API слой** (app/api/v1/endpoints/) - HTTP endpoints
4. **Глобальные обработчики** (app/main.py) - финальная обработка

---

## 1. CRUD слой (База данных)

### Принципы обработки:
- **Перехват ошибок БД**: `IntegrityError`, `SQLAlchemyError`
- **Кастомные исключения**: наследники `AppError`
- **Откат транзакций**: `await self.session.rollback()`
- **Логирование**: структурированные логи с контекстом

### Типичные паттерны:

#### 1.1 Создание записей
```python
async def create(self, user: User, data: SModel) -> Model:
    try:
        model = Model(user=user, **data.model_dump())
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model
    except IntegrityError:
        await self.session.rollback()
        raise Exception("Запись уже существует")
```

#### 1.2 Обновление записей
```python
async def update(self, model_id: UUID, data: SModel) -> Model:
    existing = await self.get_or_none(model_id=model_id)
    if not existing:
        raise ModelNotFoundError("Запись не найдена")
    
    try:
        # обновление полей
        await self.session.commit()
        await self.session.refresh(existing)
        return existing
    except IntegrityError:
        await self.session.rollback()
        raise ModelUpdateError("Ошибка при обновлении")
```

#### 1.3 Сложные операции
```python
async def complex_operation(self, data: Dict) -> Result:
    try:
        # множественные операции с БД
        result = await self._perform_operations(data)
        return result
    except Exception as e:
        await self.session.rollback()
        logger.error("Failed operation", exc_info=True)
        raise  # пробрасываем исключение наверх
```

### Кастомные исключения CRUD:
```python
# app/core/exceptions.py
class AppError(Exception):
    """Базовое исключение приложения"""

class UserAddressNotFoundError(AppError):
    """Адрес пользователя не найден"""

class UserAddressUpdateError(AppError):
    """Ошибка при обновлении адреса"""
```

---

## 2. Сервисный слой (Бизнес-логика)

### Принципы обработки:
- **Перехват CRUD исключений**: преобразование в `HTTPException`
- **Валидация бизнес-правил**: проверки перед операциями
- **Структурированное логирование**: с контекстом пользователя/операции
- **Селективный проброс**: `HTTPException` идут наверх как есть

### Типичные паттерны:

#### 2.1 Простые операции
```python
async def create_something(self, user_id: UUID, data: SCreate) -> SResponse:
    try:
        result = await self.crud.create(user_id, data)
        return SResponse.model_validate(result, from_attributes=True)
    except Exception as e:
        logger.error(
            "Failed to create something",
            extra={"user_id": str(user_id), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create something"
        )
```

#### 2.2 Операции с валидацией
```python
async def update_address(self, user_id: UUID, address_id: UUID, data: SAddress) -> SAddress:
    # Проверяем права доступа
    existing = await self.crud.get_or_none(user_id=user_id, address_id=address_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    try:
        updated = await self.crud.update(address_id=address_id, data=data)
    except UserAddressNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except UserAddressUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
    
    return SAddress.model_validate(updated, from_attributes=True)
```

#### 2.3 Селективный проброс исключений
```python
async def some_operation(self, data: SData) -> SResult:
    try:
        return await self._do_operation(data)
    except HTTPException:
        raise  # HTTPException пробрасываем как есть
    except Exception as e:
        logger.error("Operation failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed"
        )
```

---

## 3. API слой (HTTP endpoints)

### Принципы обработки:
- **Единообразие**: все endpoints следуют одному паттерну
- **Селективный проброс**: `HTTPException` идут в глобальные обработчики
- **Контекстное логирование**: с ID пользователя и параметрами запроса
- **Безопасность**: generic сообщения об ошибках для пользователей

### Стандартный паттерн endpoint:
```python
@router.post("/something", response_model=SResponse)
async def create_something(
    data: SCreate,
    current_user: User = Depends(get_current_user),
    service: SomeService = Depends(get_service),
):
    try:
        return await service.create_something(current_user.id, data)
    except HTTPException:
        raise  # HTTPException пробрасываем в глобальные обработчики
    except Exception as e:
        logger.error(
            "Failed to create something",
            extra={
                "user_id": str(current_user.id),
                "error": str(e),
                "request_data": str(data.model_dump_json())
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create something"
        )
```

### Особенности логирования в API:
- **Контекст пользователя**: всегда включаем `user_id`
- **Параметры запроса**: для отладки (осторожно с конфиденциальными данными)
- **Полный стек**: `exc_info=True` для неожиданных ошибок

---

## 4. Глобальные обработчики ошибок

### Обработчики в main.py:

#### 4.1 Ошибки валидации (422)
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = str(exc.errors())
    logger.error(f"Request validation error: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )
```

#### 4.2 HTTP исключения
```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

#### 4.3 Все остальные исключения (500)
```python
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    stack_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {error_msg}\n{stack_trace}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {error_msg}"},
    )
```

---

## Рекомендации по работе с ошибками

### 1. В CRUD слое:
- ✅ Используйте try/catch для операций с БД
- ✅ Делайте rollback при ошибках
- ✅ Создавайте кастомные исключения для специфичных ошибок
- ✅ Логируйте с контекстом операции
- ❌ Не ловите Exception без необходимости

### 2. В сервисном слое:
- ✅ Преобразуйте CRUD исключения в HTTPException
- ✅ Валидируйте бизнес-правила
- ✅ Используйте селективный проброс HTTPException
- ✅ Логируйте с контекстом пользователя
- ❌ Не скрывайте важные детали ошибок

### 3. В API слое:
- ✅ Следуйте единому паттерну обработки
- ✅ Пробрасывайте HTTPException в глобальные обработчики
- ✅ Логируйте с полным контекстом запроса
- ❌ Не обрабатывайте HTTPException повторно
- ❌ Не возвращайте внутренние детали в production

### 4. Общие принципы:
- ✅ Используйте структурированное логирование
- ✅ Включайте exc_info=True для неожиданных ошибок
- ✅ Возвращайте понятные сообщения пользователям
- ✅ Логируйте достаточно деталей для отладки
- ❌ Не дублируйте обработку на разных уровнях 