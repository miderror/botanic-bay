from passlib.context import CryptContext
import getpass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

if __name__ == "__main__":
    password = getpass.getpass("Введите пароль для админки: ")
    hashed_password = get_password_hash(password)
    print("\nВаш хэш пароля (скопируйте его в .env):")
    print(hashed_password)