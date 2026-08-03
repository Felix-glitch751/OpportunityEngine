def calculate_score(opportunity):
    score = 0

    reward = opportunity.get("reward", 0)
    trusted = opportunity.get("trusted", False)
    time_minutes = opportunity.get("time_minutes", 30)
    cost = opportunity.get("cost", 0)

    if reward >= 10000:
        score += 35
    elif reward >= 5000:
        score += 25
    elif reward >= 1000:
        score += 15

    if trusted:
        score += 30

    if time_minutes <= 10:
        score += 20
    elif time_minutes <= 20:
        score += 10

    if cost == 0:
        score += 15

    return min(score, 100)