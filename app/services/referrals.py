# In-memory store for rewarded referees (in production backed by DB unique constraint)
_REWARDED_REFEREES: set[int] = set()


def process_referral_reward(
    referrer_user_id: int,
    referee_user_id: int,
    reward_credits: int,
) -> bool:
    """
    Grants a one-time referral reward for a qualified invite.
    Must return True on initial grant, and False if already rewarded.
    """
    if referee_user_id in _REWARDED_REFEREES:
        return False

    _REWARDED_REFEREES.add(referee_user_id)
    return True
