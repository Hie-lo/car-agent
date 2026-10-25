def process_referral_reward(
    referrer_user_id: int,
    referee_user_id: int,
    reward_credits: int,
) -> bool:
    """
    Grants a one-time referral reward for a qualified invite.
    Must return True on initial qualified grant, and False if the referral was already rewarded.
    """
    raise NotImplementedError
