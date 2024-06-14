import aiofiles
import datetime
import re


async def parse_time(log_line):
    # 로그 라인에서 시간을 추출합니다.
    time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_line)
    if time_match:
        log_time_str = time_match.group(0)
        log_time = datetime.datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
        return log_time
    return None


async def time_filter(log_time, time_delta):
    # 현재 시간과 로그 시간의 차이를 계산하여 주어진 범위 내인지 확인합니다.
    if log_time and datetime.datetime.now() - log_time < time_delta:
        return True
    return False


async def filter_logs(logfile_path, duration):
    log_datas = []
    async with aiofiles.open(logfile_path, "r") as file:
        current_log = []
        log_time = None

        async for line in file:
            # 로그 라인에서 시간 패턴을 검사하여 새로운 로그 블록의 시작을 감지합니다.
            if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
                if current_log and log_time and await time_filter(log_time, duration):
                    log_text = ''.join(current_log)
                    # "root - INFO", "HTTP/1.1 500", "TimeoutError()"를 포함하는 로그를 필터링합니다.
                    if "root - INFO" in log_text or "HTTP/1.1 500" in log_text or "receive_response_headers.failed" in log_text:
                        log_datas.append(log_text.strip())

                current_log = [line]
                log_time = await parse_time(line)
            else:
                current_log.append(line)

        # 파일의 끝에 도달했을 때 남은 로그 처리
        if current_log and log_time and await time_filter(log_time, duration):
            log_text = ''.join(current_log)
            if "root - INFO" in log_text or "HTTP/1.1 500" in log_text or "receive_response_headers.failed" in log_text:
                print(log_text.strip())
                log_datas.append(log_text.strip())

    return log_datas


async def monitoring(time):
    logfile_path = "logs/server.log"  # 로그 파일 경로 지정
    duration = datetime.timedelta(minutes=time)  # 지난 24시간 동안의 로그를 검토합니다.
    datas = await filter_logs(logfile_path, duration)
    return datas