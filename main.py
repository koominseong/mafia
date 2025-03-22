import random
from player import Player


def assign_roles(players):
    # 직업 목록 정의
    mafia_jobs = ["스파이", "도둑", "과학자", "마담"]
    police_jobs = ["경찰", "요원"]
    police_job_choice = random.sample(police_jobs, 1)
    citizen_jobs = [police_job_choice[0], "의사", "정치인", "테러리스트", "군인", "건달", "간호사", "시민"]

    # 마피아 팀 4명 선정
    mafia_team = random.sample(players, 4)

    # 3명은 마피아, 1명은 마피아 특수 직업
    for i, player in enumerate(mafia_team):
        if i < 3:
            player.job = "마피아"
        else:
            player.job = random.choice(mafia_jobs)

    # 시민 팀 나머지 8명
    citizen_team = [p for p in players if p not in mafia_team]

    # 시민팀에서 8명에게 직업 할당 (중복 없음)
    assigned_jobs = random.sample(citizen_jobs, len(citizen_team))
    for player, job in zip(citizen_team, assigned_jobs):
        player.job = job



player_name = input("플레이어 이름을 입력하세요 :")


players = [
        Player(name="철수", mbti="enfj"),
        Player(name="영희", gender="woman"),
        Player(name="영수", mbti="intp"),
        Player(name="영철", mbti="estj"),
        Player(name="영호", mbti="infp"),
        Player(name="옥순", gender="woman", mbti="entj"),
        Player(name="영자", gender="woman", mbti="esfp"),
        Player(name="남수"),
        Player(name="경수", mbti="isfj"),
        Player(name="유리", gender="woman", mbti="enfp"),
        Player(name="짱구", gender="woman", mbti="istj"),
        Player(name="player_name", is_player = True)
    ]
"""==================== 게임 시작 ===================="""
# 직업 부여
assign_roles(players)

# 결과 출력
for player in players:
    print(f"{player.name} - {player.job}")

#대화
import random
from player import Player
from inputimeout import inputimeout, TimeoutOccurred

def conversation_loop(players):
    speak_count = {player: 0 for player in players}
    chat_log = []
    current_speaker = random.choice(players)
    print(f"처음 화자: {current_speaker.name}")

    # 종료 동의 상태 저장
    agree_to_end = {player: False for player in players}

    while True:
        if speak_count[current_speaker] >= 3:
            print(f"{current_speaker.name}는 더 이상 말할 수 없습니다.")
            possible = [p for p in players if speak_count[p] < 3]
            if not possible:
                print("모든 플레이어가 최대 발언 횟수를 소진했습니다.")
                break
            current_speaker = random.choice(possible)
            continue

        # 15초 안에 발언 시도
        try:
            message = inputimeout(prompt=f"[{current_speaker.name}] 말하기 (남은 {3 - speak_count[current_speaker]}회, 15초 내 입력): ", timeout=15)
        except TimeoutOccurred:
            message = f"...({current_speaker.name}의 발언 시간 초과)"

        speak_count[current_speaker] += 1
        chat_log.append({"speaker": current_speaker, "content": message})

        # 종료 투표: 아직 동의하지 않은 사람만
        if not agree_to_end[current_speaker]:
            response = input(f"{current_speaker.name}님, 대화를 종료하시겠습니까? (y/n): ").strip().lower()
            if response == "y":
                agree_to_end[current_speaker] = True

        # 모두 동의했는지 확인
        if all(agree_to_end.values()):
            print("\n모든 플레이어가 대화 종료에 동의했습니다. 종료합니다.")
            break

        # 다음 화자 후보
        possible_targets = [p for p in players if p != current_speaker and speak_count[p] < 3]
        if not possible_targets:
            print("지목할 수 있는 사람이 없습니다. 대화를 종료합니다.")
            break

        print("다음 화자로 지목할 사람을 선택하세요 (5초 내 입력):")
        for idx, p in enumerate(possible_targets):
            print(f"{idx + 1}. {p.name} (남은 {3 - speak_count[p]}회)")

        # 5초 안에 지목, 아니면 랜덤 선택
        try:
            choice = int(inputimeout(prompt="번호 입력: ", timeout=5)) - 1
            next_speaker = possible_targets[choice]
        except (TimeoutOccurred, ValueError, IndexError):
            next_speaker = random.choice(possible_targets)
            print(f"시간 초과 또는 잘못된 입력! 랜덤으로 {next_speaker.name} 지목됨.\n")

        current_speaker = next_speaker

    # 로그 출력
    print("\n[대화 종료] 전체 대화 로그:")
    for entry in chat_log:
        print(f"{entry['speaker'].name}: {entry['content']}")

#투표
def voting_phase(players):
    alive_players = [p for p in players if p.alive]
    vote_count = {p: 0 for p in alive_players}
    null_votes = 0  # 무효표 수

    print("\n [익명 투표 시작] 생존자 명단:")
    for idx, p in enumerate(alive_players):
        print(f"{idx + 1}. {p.name}")

    # 🔸 일반 투표 (본인 포함, 시간 제한 있음)
    for voter in alive_players:
        print(f"\n{voter.name}님, 투표할 대상을 선택하세요 (15초 내 입력):")
        for idx, c in enumerate(alive_players):
            print(f"{idx + 1}. {c.name}")

        try:
            choice = int(inputimeout(prompt="번호 입력: ", timeout=15)) - 1
            selected = alive_players[choice]
            vote_count[selected] += 1
            print("✅ 투표가 완료되었습니다.")
        except (TimeoutOccurred, ValueError, IndexError):
            null_votes += 1
            print("❌ 투표 시간 초과 또는 잘못된 입력! 무효표 처리됩니다.")

    # 📊 득표 결과 출력
    print("\n📊 [투표 결과 요약]")
    for p, count in vote_count.items():
        print(f"{p.name}: {count}표")
    print(f"무효표: {null_votes}표")

    max_votes = max(vote_count.values(), default=0)
    top_candidates = [p for p, count in vote_count.items() if count == max_votes]

    if len(top_candidates) == 1 and max_votes > 0:
        target = top_candidates[0]
        print(f"\n☝️ 최다 득표자: {target.name} ({max_votes}표)")

        # 🗣️ 최후의 변론 시간
        try:
            print(f"\n🗣️ {target.name}의 최후의 변론 (15초 내 입력):")
            defense = inputimeout(prompt="> ", timeout=15)
        except TimeoutOccurred:
            defense = "...(시간 초과)"

        print(f"📝 {target.name}의 발언: {defense}")

        # 👍 익명 찬반 투표
        print("\n👍 익명 찬반 투표를 시작합니다 (찬성: 처형 / 반대: 생존, 10초 내 입력)")
        agree_count = 0
        disagree_count = 0
        vote_total = 0

        for _ in alive_players:
            try:
                vote = inputimeout(prompt="투표 (y: 찬성 / n: 반대): ", timeout=10).strip().lower()
                if vote == 'y':
                    agree_count += 1
                elif vote == 'n':
                    disagree_count += 1
                else:
                    print("잘못된 입력 - 무효 처리")
                vote_total += 1
            except TimeoutOccurred:
                print("시간 초과 - 무효 처리")

        print(f"\n📊 찬반 투표 결과 (익명): 찬성 {agree_count} / 반대 {disagree_count}")

        if agree_count > disagree_count:
            target.die()
            print(f"\n☠️ {target.name}가 최종 처형되었습니다.")
        else:
            print(f"\n🙅‍♂️ {target.name}는 살아남았습니다.")

    else:
        print("\n⚠️ 동점자 발생 또는 유효표 없음! 아무도 처형되지 않습니다.")

    # ✅ 최종 상태 출력
    print("\n✅ [현재 생존 상태]")
    for p in players:
        status = "🟢 생존" if p.alive else "⚫ 사망"
        print(f"- {p.name}: {status}")
