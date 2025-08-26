import os

import utilities.lock
import pytest
import time

@pytest.fixture(scope='function')
def sleep(mocker):
    mocker.patch('utilities.lock.time.sleep')


@pytest.mark.ci
@pytest.mark.parametrize('timeout', [d/10 for d in range(5)])
class TestLockUnlock:
    @staticmethod
    def test_lock_unlock(tmp_file, timeout):
        assert os.path.exists(tmp_file) is False
        lock_fd = utilities.lock.lock(lockfile=tmp_file, timeout=timeout, delay=0.1, intent="test")
        assert os.path.exists(tmp_file) is True
        utilities.lock.unlock(lock_fd)

    @staticmethod
    def test_can_lock_again(tmp_file, timeout):
        assert utilities.lock.lock(lockfile=tmp_file, timeout=timeout, delay=0.1, intent="test") > 0
        for _ in range(int(timeout*10)):
            started = time.time()
            assert utilities.lock.lock(lockfile=tmp_file, timeout=timeout, delay=0.1, intent="test") is None
            elapsed = time.time() - started
            assert elapsed <= timeout

    @staticmethod
    def test_lock_raise_lock_timeout_if_held_by_another_pid_real_multiprocess(tmp_file, timeout):
        def worker():
            import os
            try:
                utilities.lock.lock(lockfile=tmp_file, timeout=timeout, delay=0.1, intent="test")
            except utilities.lock.LockTimeout:
                os._exit(66)

        assert utilities.lock.lock(lockfile=tmp_file, timeout=timeout, delay=0.1, intent="test") > 0
        pid = os.fork()
        if pid > 0:
            _pid, status = os.waitpid(pid, 0)
        else:
            worker()
            return

        assert status >> 8 == 66


@pytest.mark.ci
class TestCmlockWhenNoLockDir:
    @staticmethod
    def test_create_lock_dir_if_absent(tmp_path):
        assert utilities.lock.lock(lockfile=os.path.join(str(tmp_path), 'lockdir', 'lockfile')) > 0


@pytest.mark.ci
# @pytest.mark.usefixtures('sleep')
@pytest.mark.parametrize('timeout', [d/20 for d in range(10)])
class TestCmlock:
    @staticmethod
    def test_try_x_times_to_get_lock_until_it_acquires_lock(mocker, tmp_file, timeout):
        delay = 0.05
        runs = []
        side_effects = []
        min_expected_try_lock = max(0, round(timeout/delay) - 1)
        max_expected_try_lock = round(timeout/delay) + 1
        if min_expected_try_lock > 0:
            side_effects = [utilities.lock.LockAcquire({"pid": 0, "intent": ""})] * min_expected_try_lock
        # noinspection PyTypeChecker
        side_effects.append(None)

        # mocker.patch('utilities.lock.os.getpid', return_value=-1)
        lock_nowait = mocker.patch('utilities.lock.lock_nowait', side_effect=side_effects)

        started_at = time.time()
        print("try lock side effects: ", side_effects)
        print("with timout %f and delay %f expecting: (%d < try lock count <= %d) and (%f < duration <= %f)"
              % (timeout, delay, min_expected_try_lock, max_expected_try_lock, timeout - delay, timeout + delay))
        try:
            with utilities.lock.cmlock(lockfile=tmp_file, timeout=timeout, delay=delay):
                runs.append(1)
        finally:
            elapsed = time.time() - started_at
            print("found %d try lock calls elapsed: %f" % (lock_nowait.call_count, elapsed))

        assert len(runs) == 1
        assert min_expected_try_lock < lock_nowait.call_count <= max_expected_try_lock
        assert timeout - delay < elapsed <= timeout + delay, ("expecting duration: %f < duration <= %f, found %f" % (timeout - delay, timeout + delay, elapsed))

    @staticmethod
    def test_no_run_x_acquired_fails(mocker, tmp_file, timeout):
        delay = 0.05
        expected_lock_nowait = round(timeout/delay)
        side_effects = [utilities.lock.LockAcquire({"pid": 0, "intent": ""})] * (expected_lock_nowait + 1)
        mocker.patch('utilities.lock.os.getpid', return_value=-1)
        lock_nowait = mocker.patch('utilities.lock.lock_nowait', side_effect=side_effects)

        runs = []
        with pytest.raises(utilities.lock.LockTimeout):
            with utilities.lock.cmlock(lockfile=tmp_file, timeout=timeout, delay=delay):
                runs.append(1)

        assert len(runs) == 0
        assert lock_nowait.call_count <= (expected_lock_nowait + 1)


@pytest.mark.ci
class TestLockExceptions:
    @staticmethod
    def test_timeout_exc():
        """
        LockTimeOut exception
        """
        try:
            raise utilities.lock.LockTimeout(intent="test", pid=20000)
        except utilities.lock.LockTimeout as exc:
            assert exc.intent == "test"
            assert exc.pid == 20000

    @staticmethod
    def test_acquire_exc():
        """
        LockAcquire exception
        """
        try:
            raise utilities.lock.LockAcquire(intent="test", pid=20000)
        except utilities.lock.LockAcquire as exc:
            assert exc.intent == "test"
            assert exc.pid == 20000
