from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from typing import List, Optional
from datetime import date


class Estados(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    LESIONADO = "LESIONADO"
    SUSPENDIDO = "SUSPENDIDO"


class PieDominante(str, Enum):
    ZURDO = "Zurdo"
    DIESTRO = "Diestro"


class Posicion(str, Enum):
    ARQUERO = "ARQUERO"
    DEFENSA_C = "DEFENSA CENTRAL"
    DEFENSA_L = "DEFENSA LATERAL"
    VOLANTE_D = "VOLANTE DEFENSIVO"
    VOLANTE_O = "VOLANTE OFENSIVO"
    VOLANTE_C = "VOLANTE CENTRAL"
    VOLANTE_E = "VOLANTE EXTREMO"
    DELANTERO_C = "DELANTERO CENTRAL"
    DELANTERO_P = "DELANTERO PUNTA"


class TipoTarjeta(str, Enum):
    AMARILLA = "AMARILLA"
    ROJA = "ROJA"


# ========== JUGADOR ==========
class JugadorBase(SQLModel):
    nombre: str
    numero: int = Field(ge=1, le=99)
    fecha_nacimiento: date
    nacionalidad: str
    altura: float
    peso: float
    pie_dominante: PieDominante
    posicion: Posicion
    estado: Estados = Field(default=Estados.ACTIVO)
    partidos_suspension_restantes: int = Field(default=0)


class Jugador(JugadorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relaciones
    estadisticas: List["Estadistica"] = Relationship(back_populates="jugador")


class JugadorCreate(JugadorBase):
    pass


class JugadorUpdate(SQLModel):
    nombre: Optional[str] = None
    numero: Optional[int] = Field(default=None, ge=1, le=99)
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = None
    altura: Optional[float] = None
    peso: Optional[float] = None
    pie_dominante: Optional[PieDominante] = None
    posicion: Optional[Posicion] = None
    estado: Optional[Estados] = None
    partidos_suspension_restantes: Optional[int] = None


# ========== PARTIDO ==========
class PartidoBase(SQLModel):
    fecha: date
    rival: str
    goles_favor: int = Field(ge=0)
    goles_contra: int = Field(ge=0)
    resultado: Optional[str] = None


class Partido(PartidoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relaciones
    estadisticas: List["Estadistica"] = Relationship(back_populates="partido")

    def determinar_resultado(self):
        """Determina el resultado del partido"""
        if self.goles_favor > self.goles_contra:
            self.resultado = "Victoria"
        elif self.goles_favor < self.goles_contra:
            self.resultado = "Derrota"
        else:
            self.resultado = "Empate"


class PartidoCreate(PartidoBase):
    pass


class PartidoUpdate(SQLModel):
    fecha: Optional[date] = None
    rival: Optional[str] = None
    goles_favor: Optional[int] = Field(default=None, ge=0)
    goles_contra: Optional[int] = Field(default=None, ge=0)


# ========== ESTADISTICA ==========
class EstadisticaBase(SQLModel):
    jugador_id: int = Field(foreign_key="jugador.id")
    partido_id: int = Field(foreign_key="partido.id")

    # Estadísticas de participación
    minutos_jugados: int = Field(ge=0, le=120, description="Minutos jugados en el partido")

    # Estadísticas ofensivas
    goles: int = Field(default=0, ge=0, description="Goles anotados")
    asistencias: int = Field(default=0, ge=0, description="Asistencias")

    # Estadísticas disciplinarias
    faltas_cometidas: int = Field(default=0, ge=0, description="Faltas cometidas")
    tarjetas_amarillas: int = Field(default=0, ge=0, description="Tarjetas amarillas recibidas")
    tarjetas_rojas: int = Field(default=0, ge=0, description="Tarjetas rojas recibidas")


class Estadistica(EstadisticaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relaciones
    jugador: Optional[Jugador] = Relationship(back_populates="estadisticas")
    partido: Optional[Partido] = Relationship(back_populates="estadisticas")

    def calcular_suspension(self) -> int:
        """
        Calcula los partidos de suspensión basado en las tarjetas:
        - 1 tarjeta roja = 1 partido de suspensión
        - Cada 5 tarjetas amarillas acumuladas = 1 partido de suspensión
        """
        partidos_suspension = 0

        # Tarjetas rojas
        if self.tarjetas_rojas > 0:
            partidos_suspension += self.tarjetas_rojas

        # Tarjetas amarillas (cada 5 = 1 partido)
        if self.tarjetas_amarillas >= 5:
            partidos_suspension += self.tarjetas_amarillas // 5

        return partidos_suspension

    def eficiencia_goleadora(self) -> float:
        """
        Calcula la eficiencia goleadora: goles por minuto jugado
        Retorna goles por 90 minutos para facilitar comparación
        """
        if self.minutos_jugados == 0:
            return 0.0
        return (self.goles / self.minutos_jugados) * 90


class EstadisticaCreate(EstadisticaBase):
    pass


class EstadisticaUpdate(SQLModel):
    minutos_jugados: Optional[int] = Field(default=None, ge=0, le=120)
    goles: Optional[int] = Field(default=None, ge=0)
    asistencias: Optional[int] = Field(default=None, ge=0)
    faltas_cometidas: Optional[int] = Field(default=None, ge=0)
    tarjetas_amarillas: Optional[int] = Field(default=None, ge=0)
    tarjetas_rojas: Optional[int] = Field(default=None, ge=0)


# ========== MODELOS DE RESPUESTA ==========
class JugadorConEstadisticas(JugadorBase):
    """Modelo para respuesta con estadísticas del jugador"""
    id: int
    total_partidos: int = 0
    total_minutos: int = 0
    total_goles: int = 0
    total_asistencias: int = 0
    total_tarjetas_amarillas: int = 0
    total_tarjetas_rojas: int = 0
    promedio_minutos: float = 0.0
    eficiencia_goleadora: float = 0.0


class PartidoConEstadisticas(PartidoBase):
    """Modelo para respuesta con estadísticas del partido"""
    id: int
    jugadores_participantes: int = 0
    total_minutos_jugados: int = 0