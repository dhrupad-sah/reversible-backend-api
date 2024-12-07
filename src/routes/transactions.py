from fastapi import APIRouter, HTTPException
from ..types.transaction import ReverseTransactionRequest, TransferRequest, ForceApprovalRequest
from ..db.supabase import supabase_client
from ..utils.coinbase import call_contract_function, read_contract_function, WalletType

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.post("/transfer")       
async def transfer_money(wallet: WalletType, transfer: TransferRequest):
    try:
        transfer_result = call_contract_function(wallet, "transfer", {"to": transfer.to_wallet, "amount": transfer.amount})
        if transfer_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Transfer failed")
        transfer.amount = int(transfer.amount)
        transfer_index = read_contract_function(wallet, "getTransferCount", {"from": wallet.address_id, "to": transfer.to_wallet})  
        if transfer_index.get('success') != True:
            raise HTTPException(status_code=500, detail="Transfer index failed")
        transaction_data = {
            "from_wallet": wallet.address_id,
            "to_wallet": transfer.to_wallet,
            "amount": transfer.amount,
            "state": "pending",
            "index": transfer_index["result"]-1
        }
        transaction = supabase_client.table("transactions").insert(transaction_data).execute()
        
        # Get current balances
        sender = supabase_client.table("users").select("nrb_value").eq("wallet_address", wallet.address_id).execute()
        recipient = supabase_client.table("users").select("rb_value").eq("wallet_address", transfer.to_wallet).execute()
        
        # Calculate new balances
        new_sender_balance = sender.data[0]["nrb_value"] - transfer.amount
        new_recipient_balance = recipient.data[0]["rb_value"] + transfer.amount
        
        # Update sender's NRB balance
        supabase_client.table("users")\
            .update({"nrb_value": new_sender_balance})\
            .eq("wallet_address", wallet.address_id)\
            .execute()
        
        # Update recipient's RB balance
        supabase_client.table("users")\
            .update({"rb_value": new_recipient_balance})\
            .eq("wallet_address", transfer.to_wallet)\
            .execute()
        
        return {"status": "success", "transaction_id": transaction.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/force-approval")
async def force_approval(wallet: WalletType, request: ForceApprovalRequest):
    try:
        transaction_index = supabase_client.table("transactions")\
            .select("index")\
            .eq("id", request.transaction_id)\
            .execute()
        fast_withdraw_result = call_contract_function(wallet, "fastWithdraw", {"index": transaction_index.data[0].get("index"), "from": wallet.address_id, "to": request.to_wallet})
        if fast_withdraw_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Fast withdraw failed")
        transaction = supabase_client.table("transactions").select("*").eq("id", request.transaction_id).execute()

        recipient = request.to_wallet
        amount = transaction.data[0]["amount"]

        recipient_balance = supabase_client.table("users").select("rb_value, nrb_value").eq("wallet_address", recipient).execute()

        current_rb = recipient_balance.data[0]["rb_value"]
        current_nrb = recipient_balance.data[0]["nrb_value"]

        supabase_client.table("users")\
            .update({
                "rb_value": current_rb - amount,
                "nrb_value": current_nrb + amount
            })\
            .eq("wallet_address", recipient)\
            .execute()

        transaction_update = supabase_client.table("transactions")\
            .update({"state": "completed"})\
            .eq("id", request.transaction_id)\
            .execute()
        
        return {"status": "success", "message": "Transaction force approved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
