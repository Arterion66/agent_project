from typing import List, Dict
from pydantic import BaseModel

class NameDict(BaseModel):
    name: str

class AbilitySummary(BaseModel):
    ability: NameDict
    is_hidden: bool

class Stats(BaseModel):
    base_stat: int
    stat: NameDict

class Type(BaseModel):
    type: NameDict

class Move(BaseModel):
    move: NameDict

class PokemonSchemaAPI(BaseModel):
    id: int
    is_default: bool
    name: str
    abilities: List[AbilitySummary]
    height: int
    weight: int
    stats: List[Stats]
    types: List[Type]
    moves: List[Move]

class FlattenedAbility(BaseModel):
    name: str
    is_hidden: bool

class PokemonSchema(BaseModel):
    id: int
    is_default: bool
    name: str
    abilities: List[FlattenedAbility]
    height: int
    weight: int
    stats: List[Dict[str, int]]
    types: List[str]
    moves: List[str]

    @classmethod
    def from_api(cls, api_model: PokemonSchemaAPI) -> "PokemonSchema":
        flattened_abilities = [
            FlattenedAbility(name=ab.ability.name, is_hidden=ab.is_hidden)
            for ab in api_model.abilities
        ]
        flattened_types = [t.type.name for t in api_model.types]
        flattened_stats = [{s.stat.name: s.base_stat} for s in api_model.stats]
        flattened_moves = [m.move.name for m in api_model.moves]

        return cls(
            id=api_model.id,
            is_default=api_model.is_default,
            name=api_model.name,
            abilities=flattened_abilities,
            height=api_model.height,
            weight=api_model.weight,
            stats=flattened_stats,
            types=flattened_types,
            moves=flattened_moves,
        )
