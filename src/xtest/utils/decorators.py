import time
import typing as t


class WaitError(Exception):
    pass


def wait(
    method: t.Callable[..., t.Any],
    *,
    error: t.Union[t.Type[Exception], t.Tuple[t.Type[Exception], ...]] = Exception,
    timeout: int = None,
    check: bool = False,
    interval: float = 0.5,
    raise_exception: bool = True,
    args: tuple = (),
    kwargs: dict[str, t.Any] = None,
) -> t.Optional[t.Any]:
    """Кастомный декоратор для вызова функции несколько раз в течении определенного времени.

    Args:
        method (typing.Callable[..., t.Any]): функция для вызова.
        error (t.Union[t.Type[Exception], t.Tuple[t.Type[Exception], ...]]): ошибки для игнорирования.
        timeout (int): таймаут для ожидания.
        check (bool): проверка результата. При отсутствии результата вызывается TimeoutException.
        interval (float): интервал для ожидания.
        raise_exception (bool): вызывается ли ошибка после завершения функции.
        args (tuple): дополнительные позиционные аргументы для передачу в функцию.
        kwargs (dict): дополнительные аргументы по ключу для передачу в функцию.

    Returns:
        typing.Optional[typing.Any]: результат функции.
    """
    if not isinstance(error, type):
        errors = tuple(error)
    else:
        errors = (error,)
    last_cls = None
    if timeout is None:
        timeout = 10

    start_time = time.time()
    while time.time() - start_time < int(timeout):
        try:
            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}
            result = method(*args, **kwargs)
            if check:
                if result is not None:
                    return result
                last_cls = WaitError("Результат не должен быть None!")
            else:
                return result
        except errors as exception:
            last_cls = exception
        time.sleep(interval)

    if raise_exception:
        raise last_cls
    return None
