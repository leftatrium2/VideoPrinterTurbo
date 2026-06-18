from utils import const


def result_succ(data: object) -> dict:
    return {
        'code': const.GLOBAL_SUCC,
        'msg': 'success',
        'data': data
    }


def result_failure(code: int, message: str):
    return {
        'code': code,
        'msg': message,
        'data': {}
    }
