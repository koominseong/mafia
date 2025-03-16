import random
from player import Player


def assign_roles(players):
    # 직업 목록 정의
    mafia_jobs = ["스파이", "도둑", "과학자", "마담"]
    citizen_jobs = ["경찰", "요원", "의사", "정치인", "테러리스트", "군인", "건달", "간호사", "시민"]

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
        Player(name="정숙", gender="woman", mbti="istj"),
        Player(name="짱구", mbti="enfp")
    ]

# 역할 배정
assign_roles(players)

# 결과 출력
for player in players:
    print(f"{player.name} - {player.job}")