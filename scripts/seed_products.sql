-- Очистка таблиц
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE categories CASCADE;

-- Создание категорий
INSERT INTO categories (id, name, description, created_at, updated_at) VALUES
('a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'Витамины', 'Витамины для поддержания здоровья', NOW(), NOW()),
('b2c3d4e5-f6a7-4b2c-9d3e-4f5a6b7c8d9e', 'Омега', 'Незаменимые жирные кислоты', NOW(), NOW()),
('c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'Минералы', 'Минералы и микроэлементы', NOW(), NOW()),
('d4e5f6a7-b8c9-4d4e-1f5a-6b7c8d9e0f1a', 'Коллаген', 'Коллаген для суставов и кожи', NOW(), NOW()),
('e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'Антиоксиданты', 'Антиоксиданты для защиты клеток', NOW(), NOW()),
('f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'Нейротоники', 'Добавки для работы мозга', NOW(), NOW()),
('a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'Спортивное питание', 'Добавки для спортсменов', NOW(), NOW());

-- Вставка продуктов с привязкой к категориям
INSERT INTO products (
    id,
    name,
    description,
    price,
    stock,
    is_active,
    category_id,
    image_url,
    sku,
    created_at,
    updated_at
) VALUES
('c19d1f53-5a03-4f44-9f3e-6c90724d3d6d', 'Витамин C 1000мг', 'Витамин C с шиповником способствует укреплению иммунитета и снижению утомляемости. 100 таблеток.', 999.99, 100, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/c1000.jpg', 'VIT-C1000-100', NOW(), NOW()),
('d2f9d1a3-8f4b-4f1a-9c2d-7c88f3b2d6e4', 'Омега-3', 'Рыбий жир высокой очистки, поддерживает здоровье сердца и сосудов. 60 капсул.', 1299.99, 75, true, 'b2c3d4e5-f6a7-4b2c-9d3e-4f5a6b7c8d9e', 'https://placeholder.com/omega/3-60.jpg', 'OMEGA-3-60', NOW(), NOW()),
('e3a8c2b4-7d5e-4f2b-8c1e-9d7f4a3e2d1b', 'Магний B6', 'Магний с витамином B6 способствует снижению утомляемости и поддержанию работы нервной системы. 50 таблеток.', 799.99, 150, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/mg-b6-50.jpg', 'MG-B6-50', NOW(), NOW()),
('f4b9d2c5-6e4a-4d3b-9f2e-7c88f3b2d6e5', 'Коллаген', 'Коллаген с витамином C для укрепления суставов и кожи. 120 капсул.', 1499.99, 80, true, 'd4e5f6a7-b8c9-4d4e-1f5a-6b7c8d9e0f1a', 'https://placeholder.com/collagen/collagen-120.jpg', 'COLLAGEN-120', NOW(), NOW()),
('a5c2d4e6-7f8a-4b3d-9e2f-6c88f3b2d6e6', 'Коэнзим Q10', 'Антиоксидант, поддерживающий здоровье сердца и повышающий уровень энергии. 60 капсул.', 1799.99, 90, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/coenzyme/q10-60.jpg', 'COQ10-60', NOW(), NOW()),
('b6d3e5f7-8c9a-4c2d-9f1e-7c88f3b2d6e7', 'Цинк', 'Цинк для поддержания иммунитета и здоровья кожи. 50 таблеток.', 599.99, 200, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/zinc-50.jpg', 'ZINC-50', NOW(), NOW()),
('c7e4f6a8-9d2a-4d3c-9f0e-6c88f3b2d6e8', 'Витамин D3', 'Витамин D3 2000 МЕ для поддержки иммунитета и костной системы. 90 капсул.', 899.99, 120, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/d3-2000.jpg', 'VIT-D3-2000', NOW(), NOW()),
('d8f5a7c9-2b3a-4e4d-9f2e-7c88f3b2d6e9', 'Биотин', 'Биотин для здоровья волос, кожи и ногтей. 100 таблеток.', 749.99, 160, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/biotin-100.jpg', 'BIOTIN-100', NOW(), NOW()),
('e976a8a2-3456-4f5d-9e2f-6c88f3b2d6ea', 'Лецитин', 'Лецитин для поддержки работы мозга и нервной системы. 120 капсул.', 1199.99, 110, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/lecithin-120.jpg', 'LECITHIN-120', NOW(), NOW()),
('f0a7a9f3-4567-476d-9f1e-7c88f3b2d6eb', 'Железо', 'Железо для профилактики анемии и поддержания уровня гемоглобина. 60 таблеток.', 699.99, 140, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/iron-60.jpg', 'IRON-60', NOW(), NOW()),
('a1a8a0b4-5678-4a7d-9f2e-6c88f3b2d6ec', 'Йод', 'Йод для нормального функционирования щитовидной железы. 100 таблеток.', 499.99, 180, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/iodine-100.jpg', 'IODINE-100', NOW(), NOW()),
('b2b9c1d5-6789-4a8d-9e2f-7c88f3b2d6ed', 'Хром', 'Хром для поддержания уровня сахара в крови. 90 таблеток.', 549.99, 130, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/chromium-90.jpg', 'CHROMIUM-90', NOW(), NOW()),
('a3b0c2d6-7890-4b9d-9f1e-6c88f3b2d6ee', 'Фолиевая кислота', 'Фолиевая кислота для поддержания кроветворения и беременности. 60 таблеток.', 399.99, 220, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/folic-60.jpg', 'FOLIC-60', NOW(), NOW()),
('c4d1e3f7-8901-4c0d-9e2f-7c88f3b2d6ef', 'L-Карнитин', 'L-Карнитин для поддержки метаболизма и сжигания жира. 90 капсул.', 1599.99, 70, true, 'a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'https://placeholder.com/sport/l-carnitine-90.jpg', 'LCARNITINE-90', NOW(), NOW()),


('d5e2f4a8-9012-4d1e-9f2e-7c88f3b2d6f0', 'Витамин B-комплекс', 'Комплекс витаминов группы B для поддержки энергетического обмена. 90 капсул.', 899.99, 150, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/b-complex-90.jpg', 'B-COMPLEX-90', NOW(), NOW()),

('e6f3a5b9-0123-4e2f-9f1e-7c88f3b2d6f1', 'Селен', 'Селен с витамином E для антиоксидантной защиты. 60 таблеток.', 649.99, 130, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/selenium-60.jpg', 'SELENIUM-60', NOW(), NOW()),

('f7a4b6c0-1234-4f3a-9e2f-7c88f3b2d6f2', 'Глюкозамин с Хондроитином', 'Комплекс для поддержки здоровья суставов. 120 таблеток.', 1799.99, 85, true, 'd4e5f6a7-b8c9-4d4e-1f5a-6b7c8d9e0f1a', 'https://placeholder.com/collagen/glucosamine-120.jpg', 'GLUCOS-CHOND-120', NOW(), NOW()),

('a8b5c7d1-2345-4a4b-9f1e-7c88f3b2d6f3', 'Омега-3-6-9', 'Комплекс незаменимых жирных кислот. 90 капсул.', 1499.99, 95, true, 'b2c3d4e5-f6a7-4b2c-9d3e-4f5a6b7c8d9e', 'https://placeholder.com/omega/369-90.jpg', 'OMEGA-369-90', NOW(), NOW()),

('b9c6d8e2-3456-4b5c-9e2f-7c88f3b2d6f4', 'Гинкго Билоба', 'Экстракт для улучшения памяти и концентрации. 60 капсул.', 899.99, 120, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/ginkgo-60.jpg', 'GINKGO-60', NOW(), NOW()),

('c0d7e9f3-4567-4c6d-9f1e-7c88f3b2d6f5', 'Пробиотики', 'Комплекс полезных бактерий для здоровья кишечника. 30 капсул.', 1299.99, 70, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/probiotics-30.jpg', 'PROBIO-30', NOW(), NOW()),

('d1e8f0a4-5678-4d7e-9e2f-7c88f3b2d6f6', 'Кальций D3 K2', 'Комплекс для укрепления костей. 90 таблеток.', 999.99, 110, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/calcium-d3k2-90.jpg', 'CALC-D3K2-90', NOW(), NOW()),

('e2f9a1b5-6789-4e8f-9f1e-7c88f3b2d6f7', 'Ресвератрол', 'Мощный антиоксидант из красного винограда. 60 капсул.', 1599.99, 65, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/resveratrol-60.jpg', 'RESVER-60', NOW(), NOW()),

('f3a0b2c6-7890-4f9a-9e2f-7c88f3b2d6f8', 'BCAA', 'Аминокислоты с разветвленной цепью для спортсменов. 200 капсул.', 1899.99, 80, true, 'a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'https://placeholder.com/sport/bcaa-200.jpg', 'BCAA-200', NOW(), NOW()),

('a4b1c3d7-8901-4a0b-9f1e-7c88f3b2d6f9', 'Мелатонин', 'Для нормализации сна. 60 таблеток.', 699.99, 140, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/melatonin-60.jpg', 'MELAT-60', NOW(), NOW()),

('b5c2d4e8-9012-4b1c-9e2f-7c88f3b2d6a0', 'MSM', 'Метилсульфонилметан для суставов и связок. 120 капсул.', 899.99, 95, true, 'd4e5f6a7-b8c9-4d4e-1f5a-6b7c8d9e0f1a', 'https://placeholder.com/collagen/msm-120.jpg', 'MSM-120', NOW(), NOW()),

('c6d3e5f9-0123-4c2d-9e2f-7c88f3b2d6a1', 'Витамин E', 'Природный антиоксидант. 100 капсул.', 799.99, 130, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/vit-e-100.jpg', 'VIT-E-100', NOW(), NOW()),

('d7e4f6a0-1234-4d3e-9e2f-7c88f3b2d6a2', 'Спирулина', 'Натуральный источник белка и микроэлементов. 120 таблеток.', 999.99, 85, true, 'a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'https://placeholder.com/sport/spirulina-120.jpg', 'SPIR-120', NOW(), NOW()),

('e8f5a7b1-2345-4e4f-9f1e-7c88f3b2d6a3', 'Таурин', 'Аминокислота для поддержки сердечно-сосудистой системы. 90 капсул.', 699.99, 110, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/taurine-90.jpg', 'TAUR-90', NOW(), NOW()),

('f9a6b8c2-3456-4f5a-9e2f-7c88f3b2d6a4', 'Кальций Магний Цинк', 'Комплекс минералов. 100 таблеток.', 849.99, 140, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/ca-mg-zn-100.jpg', 'CA-MG-ZN-100', NOW(), NOW()),

('a0b7c9d3-4567-4a6b-9f1e-7c88f3b2d6a5', 'Гиалуроновая кислота', 'Для здоровья кожи и суставов. 60 капсул.', 1399.99, 75, true, 'd4e5f6a7-b8c9-4d4e-1f5a-6b7c8d9e0f1a', 'https://placeholder.com/collagen/hyaluronic-60.jpg', 'HYAL-60', NOW(), NOW()),

('b1c8d0e4-5678-4b7c-9e2f-7c88f3b2d6a6', 'Витамин A', 'Для здоровья зрения и иммунитета. 60 капсул.', 599.99, 120, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/vit-a-60.jpg', 'VIT-A-60', NOW(), NOW()),

('c2d9e1f5-6789-4c8d-9f1e-7c88f3b2d6a7', 'Креатин', 'Для увеличения силы и мышечной массы. 300г.', 1299.99, 90, true, 'a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'https://placeholder.com/sport/creatine-300.jpg', 'CREAT-300', NOW(), NOW()),

('d3e0f2a6-7890-4d9e-9e2f-7c88f3b2d6a8', 'Астаксантин', 'Мощный антиоксидант. 30 капсул.', 1599.99, 60, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/astax-30.jpg', 'ASTAX-30', NOW(), NOW()),

('e4f1a3b7-8901-4e0f-9f1e-7c88f3b2d6a9', 'Пиколинат хрома', 'Для контроля уровня сахара. 60 таблеток.', 649.99, 130, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/chromium-pic-60.jpg', 'CR-PIC-60', NOW(), NOW()),

('f5a2b4c8-9012-4f1a-9e2f-7c88f3b2d6b0', 'Глутамин', 'Аминокислота для восстановления. 200г.', 999.99, 85, true, 'a7b8c9d0-e1f2-4a7b-4c8d-9e0f1a2b3c4d', 'https://placeholder.com/sport/glutamine-200.jpg', 'GLUT-200', NOW(), NOW()),

('a6b3c5d9-0123-4a2b-9f1e-7c88f3b2d6b1', 'Комплекс антиоксидантов', 'Смесь мощных антиоксидантов. 90 капсул.', 1299.99, 70, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/complex-90.jpg', 'ANTIOX-90', NOW(), NOW()),

('b7c4d6e0-1234-4b3c-9e2f-7c88f3b2d6b2', 'Рыбий жир DHA', 'Концентрированный DHA для мозга. 60 капсул.', 1499.99, 95, true, 'b2c3d4e5-f6a7-4b2c-9d3e-4f5a6b7c8d9e', 'https://placeholder.com/omega/dha-60.jpg', 'DHA-60', NOW(), NOW()),

('c8d5e7f1-2345-4c4d-9f1e-7c88f3b2d6b3', '5-HTP', 'Для улучшения настроения. 60 капсул.', 899.99, 110, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/5htp-60.jpg', '5HTP-60', NOW(), NOW()),

('d9e6f8a2-3456-4d5e-9e2f-7c88f3b2d6b4', 'Витамин K2', 'Для костей и сердечно-сосудистой системы. 60 капсул.', 799.99, 120, true, 'a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d', 'https://placeholder.com/vitamins/k2-60.jpg', 'VIT-K2-60', NOW(), NOW()),

('e0f7a9b3-4567-4e6f-9f1e-7c88f3b2d6b5', 'NAC', 'N-ацетилцистеин для детоксикации. 90 капсул.', 899.99, 100, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/nac-90.jpg', 'NAC-90', NOW(), NOW()),

('f1a8b0c4-5678-4f7a-9e2f-7c88f3b2d6b6', 'Кверцетин', 'Природный флавоноид. 60 капсул.', 1099.99, 90, true, 'e5f6a7b8-c9d0-4e5f-2a6b-7c8d9e0f1a2b', 'https://placeholder.com/antioxidants/quercetin-60.jpg', 'QUERC-60', NOW(), NOW()),

('a2b9c1d5-6789-4a8b-9f1e-7c88f3b2d6b7', 'Бор', 'Минерал для костей и гормонального баланса. 100 таблеток.', 549.99, 150, true, 'c3d4e5f6-a7b8-4c3d-0e4f-5a6b7c8d9e0f', 'https://placeholder.com/minerals/boron-100.jpg', 'BORON-100', NOW(), NOW()),

('b3c0d2e6-7890-4b9c-9e2f-7c88f3b2d6b8', 'Фосфатидилсерин', 'Для когнитивных функций. 60 капсул.', 1699.99, 70, true, 'f6a7b8c9-d0e1-4f6a-3b7c-8d9e0f1a2b3c', 'https://placeholder.com/neuro/ps-60.jpg', 'PS-60', NOW(), NOW());





UPDATE public.products 
SET additional_images_urls = '{/media/products/21a36a0d-61ec-42db-b3bd-7cef98d945f8.png}';

UPDATE public.products 
SET image_url = '/media/products/4d33526f-f80c-4f47-9b65-3d91035abb28.png';

UPDATE public.products 
SET additional_description = 'Состав:
Омега-3 жирные кислоты (ЭПК и ДГК) из рыбьего жира высокой очистки. Омега-6 жирные кислоты (линолевая кислота) из масла бурачника и примулы вечерней. Омега-9 жирные кислоты (олеиновая кислота) из оливкового масла. Витамин Е (токоферол) как природный антиоксидант. Желатиновая оболочка капсулы. Очищенная вода.

Преимущества:
Поддерживает здоровье сердечно-сосудистой системы. Способствует улучшению работы мозга и укреплению памяти. Помогает поддерживать нормальный уровень холестерина. Благотворно влияет на состояние кожи, волос и ногтей. Поддерживает здоровье суставов и снижает воспалительные процессы. Укрепляет иммунную систему. Способствует здоровому развитию плода во время беременности. Помогает поддерживать острое зрение. Производится из высококачественного сырья с использованием современных технологий очистки. Не содержит искусственных красителей и консервантов.';