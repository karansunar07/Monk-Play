import sys

from . import authcontroller as authController
from .authcontroller import login_page, login_user, register_page, register_user
from .database import get_db_connection


sys.modules[f"{__name__}.authController"] = authController

__all__ = [
    "authController",
    "get_db_connection",
    "login_page",
    "login_user",
    "register_page",
    "register_user",
]
