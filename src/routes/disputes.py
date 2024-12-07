from fastapi import APIRouter, HTTPException
from ..types.transaction import DisputeRequest
from ..db.supabase import supabase_client
from ..utils.coinbase import call_contract_function, WalletType, read_contract_function, read_governance_function

router = APIRouter(
    prefix="/disputes",
    tags=["disputes"]
)
@router.post("/raise-dispute")
async def raise_dispute(wallet: WalletType, request: DisputeRequest):
    try:
        transaction_index = supabase_client.table("transactions")\
            .select("index")\
            .eq("id", request.transaction_id)\
            .execute()
        print(transaction_index.data[0].get("index"))
        dispute_result = call_contract_function(wallet, "raiseDispute", {"index": transaction_index.data[0].get("index"), "from": wallet.address_id, "to": request.to_wallet})
        if dispute_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Dispute failed")
        
        dispute_count = read_governance_function(wallet, "getDisputeCount", {})
        print(dispute_count)
        # Update transaction state to "disputed"
        transaction_update = supabase_client.table("transactions")\
            .update({"state": "disputed"})\
            .eq("id", request.transaction_id)\
            .execute()
        
        # Create new dispute entry
        dispute_data = {
            "transactionId": request.transaction_id,
            "intendedRecipient": request.to_wallet,
            "proof_title": request.proofTitle,
            "proof_content": request.proofContent,
            "verdict": False,
            "dispute_count": dispute_count.get("result")
        }
        supabase_client.table("disputes").insert(dispute_data).execute()
        
        return {"status": "success", "message": "Dispute raised successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get-disputes")
async def get_disputes():
    try:
        disputes = supabase_client.table("disputes").select("*").execute()
        return {"status": "success", "data": disputes.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
