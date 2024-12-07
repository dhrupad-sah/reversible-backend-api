from fastapi import APIRouter, HTTPException
from ..db.supabase import supabase_client
from ..types.user import VoteRequest
from ..utils.coinbase import call_contract_function, WalletType, call_governance_function

router = APIRouter(
    prefix="/judges",
    tags=["judges"]
)

@router.post("/vote")
async def vote(wallet: WalletType, request: VoteRequest):
    try:
        dispute_count = supabase_client.table("disputes").select("dispute_count").eq("id", request.dispute_id).execute()
        vote_result = call_governance_function(wallet, "voteAndResolve", {"_disputeId": dispute_count.data[0].get("dispute_count"), "_support": request.vote})
        if vote_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Vote failed")
        return {"status": "success", "message": "Vote submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    