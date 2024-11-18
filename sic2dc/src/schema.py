from enum import Enum
from pydantic import BaseModel, StrictStr


class CureActionEnum(str, Enum):
    enter_exit = 'enter_exit'


class FilterActionEnum(str, Enum):
    cp21 = "cp21"
    cp12 = "cp12"
    del1 = "del1"
    del2 = "del2"
    upd1 = "upd1"
    upd2 = "upd2"


class When(BaseModel):
    has_children: list[StrictStr] | None = None
    doesnt_have_chidren: list[StrictStr] | None = None
    absent_in_destination: bool | None = None


class CfgCmprCure(BaseModel):
    action: CureActionEnum
    kwargs: dict | None = dict()


class CfgCmprFilter(BaseModel):
    action: FilterActionEnum
    when: list[When] = []
    path: list[StrictStr] = []
    data: dict = dict()


class CfgCmprSettings(BaseModel):
    indent_char: str
    indent: int
    comments: list[StrictStr]
    ignore_cmd_nocmd: bool = False
    no_cmd: str | None = None
