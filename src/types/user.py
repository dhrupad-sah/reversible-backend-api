from pydantic import BaseModel

class UserAuth(BaseModel):
    email: str

class DepositRequest(BaseModel):
    wallet_address: str
    amount: float

class UserBalance(BaseModel):
    wallet_address: str
    rb_value: float = 0
    nrb_value: float = 0

class ClaimRewardsRequest(BaseModel):
    transaction_id: str

class DepositRequest(BaseModel):
    amount: str

