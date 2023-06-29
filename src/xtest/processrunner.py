import os
import signal
import types


class ProcessRunner:

    @property
    def pid(self) -> int:
        return self.__pid

    def run_process(self, process_module: types.ModuleType) -> None:
        process = Popen(
            process_module.__process_cmd_start__,
            stdin=self.__stdin,
            stdout=self.__stdout,
            stderr=self.__stderr,
        )

        if process.returncode is not None:
            os.kill(process.pid, signal.SIGINT)
            raise SetupProcessError(reason="Процесс запустился с ошибкой. Проверьте логи по пути")

        if hasattr(self.__config, "run_subprocesses") and isinstance(self.__config.run_subprocesses, list):
            self.__config.run_subprocesses.append(self)
        else:
            self.__config.run_subprocesses = [self]

        self.__pid = process.pid

    def teardown_process(self):
        os.kill(self.pid, signal.SIGKILL)
        self.__stdin.close()
        self.__stdout.close()
        self.__stderr.close()
