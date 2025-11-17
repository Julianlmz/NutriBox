from passlib.context import CryptContext

# Usamos bcrypt, que es el estándar
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verificar_password(password_plano: str, password_hasheado: str) -> bool:
    """
    Compara un password en texto plano con uno hasheado.
    """
    return pwd_context.verify(password_plano, password_hasheado)


def hashear_password(password: str) -> str:
    """
    Convierte un password de texto plano a un hash.
    """
    return pwd_context.hash(password)