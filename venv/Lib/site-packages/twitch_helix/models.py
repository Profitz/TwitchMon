from dataclasses import dataclass


def decode(data, cls):
    if isinstance(data, cls):
        return data
    kwargs = {}
    for key, value in data.items():
        member_type = cls.__annotations__[key]
        member = decode(value, member_type)
        kwargs[key] = member
    return cls(**kwargs)


class Model:
    @classmethod
    def from_json(cls, data: dict):
        return decode(data, cls)

    def to_json(self, encode_none: bool = False):
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Model):
                data[key] = value.to_json(encode_none)
            elif value is None:
                if encode_none:
                    data[key] = None
            # TODO handle all primitive types
            elif isinstance(value, int) or isinstance(value, str):
                data[key] = value
            else:
                raise ValueError('bad type')
        return data


@dataclass
class ChannelInfo(Model):
    broadcaster_id: str = None
    broadcaster_name: str = None
    game_name: str = None
    game_id: str = None
    broadcaster_language: str = None
    title: str = None
    delay: int = None


@dataclass
class Reward(Model):
    id: str
    title: str
    prompt: str
    cost: int


@dataclass
class RewardRedemption(Model):
    broadcaster_name: str
    broadcaster_login: str
    broadcaster_id: str
    id: str
    user_id: str
    user_name: str
    user_login: str
    user_input: str
    status: str
    redeemed_at: str
    reward: Reward


@dataclass
class Condition(Model):
    pass


@dataclass
class BroadcasterCondition(Condition):
    broadcaster_user_id: str


@dataclass
class FromToCondition(Condition):
    from_broadcaster_user_id: str = None
    to_broadcaster_user_id: str = None


@dataclass
class RewardCondition(Condition):
    broadcaster_user_id: str
    reward_id: str = None


@dataclass
class Transport(Model):
    method: str
    callback: str
    secret: str
