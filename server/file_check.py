import paramiko
import argparse

# [Source] Server 1 info
SERVER1_USER = 'SOURCE_USER'
SERVER1_IP = 'SOURCE_IP'
SERVER1_PORT = 22
SOURCE_DIR = 'SOURCE_PATH'

# [Dest] Server 2 info 
SERVER2_USER = 'DEST_USER'
SERVER2_IP = 'DEST_IP'
SERVER2_PORT = 22
DEST_DIR = SOURCE_DIR # .replace('/mnt', '')

def create_ssh_client(host, port, username, password=None):
    ''' SSH client 생성 '''
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password)
    return client

def execute_command(ssh_client, command, password):
    ''' SSH에서 명령어 실행 '''
    
    # source_pw와 dest_pw를 사용하여 명령어에 비밀번호 적용
    if password:
        command = f'echo {password} | sudo -S {command}'

    print('command check: ', command)
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()

    return output.strip(), error.strip()

def compare_directories(ssh_server1, ssh_server2, source_pw, dest_pw):
    ''' 서버에서 직접 diff 실행 '''

    print('\n📌 두 서버에서 직접 파일 비교 실행 중...\n')

    # 각 서버에서 파일 리스트 가져오기
    #cmd_ls = f'find {SOURCE_DIR} -type f | sort'
    cmd_ls = f"find {SOURCE_DIR} -type f ! -path '*/.vscode-server/*'| sort"  # ignore */.vscode-server/*
    
    print(f'📂 서버1에서 파일 목록 가져오는 중...')
    files_server1, error1 = execute_command(ssh_server1, cmd_ls, source_pw)
    files_server1 = files_server1.replace('/mnt', '')
    
    print(f'📂 서버2에서 파일 목록 가져오는 중...')
    files_server2, error2 = execute_command(ssh_server2, cmd_ls.replace(SOURCE_DIR, DEST_DIR), dest_pw)

    # if error1 or error2:
    #     print(f'⚠️ 오류 발생!\n서버1 오류: {error1}\n서버2 오류: {error2}')
        
    # 서버 간 파일 리스트 비교
    if files_server1 != files_server2:
        print('❌ 파일 구조가 다릅니다! 차이점:')
        set1 = set(files_server1.split('\n'))
        set2 = set(files_server2.split('\n'))
        
        only_in_server1 = set1 - set2
        only_in_server2 = set2 - set1
        
        if only_in_server1:
            print('\n🔴 서버1에만 존재하는 파일:')
            print(len(only_in_server1))
        
        if only_in_server2:
            print('\n🔵 서버2에만 존재하는 파일:')
            print(len(only_in_server2))
        
        return

    print('✅ 파일 구조가 동일합니다. 내용 비교 시작...')

def main():
    # Argument parser 설정
    parser = argparse.ArgumentParser(description='서버 간 파일 비교')
    parser.add_argument('-s', '--source_pw', type=str, required=True, help='서버1의 비밀번호')
    parser.add_argument('-d', '--dest_pw', type=str, required=True, help='서버2의 비밀번호')
    args = parser.parse_args()

    # 비밀번호 받아오기
    source_pw = args.source_pw
    dest_pw = args.dest_pw

    print('🔗 Source 서버 연결 중...')
    ssh_server1 = create_ssh_client(SERVER1_IP, SERVER1_PORT, SERVER1_USER, password=source_pw)

    print('🔗 Destination 서버 연결 중...')
    ssh_server2 = create_ssh_client(SERVER2_IP, SERVER2_PORT, SERVER2_USER, password=dest_pw)

    try:
        compare_directories(ssh_server1, ssh_server2, source_pw, dest_pw)
    finally:
        ssh_server1.close()
        ssh_server2.close()
        print('🔌 SSH 연결 종료.')

if __name__ == '__main__':
    main()
