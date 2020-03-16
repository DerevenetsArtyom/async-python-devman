from collections import Counter


async def convert_sms_data(sms_data):
    """Convert sms related data from Redis format to format supported by frontend"""
    phones_counter = Counter(sms_data["phones"].values())
    return {
        "timestamp": sms_data.get("created_at"),
        "SMSText": sms_data.get("text"),
        "mailingId": str(sms_data.get("sms_id")),
        "totalSMSAmount": sms_data.get("phones_count"),
        "deliveredSMSAmount": phones_counter.get("delivered", 0),
        "failedSMSAmount": phones_counter.get("failed", 0),
    }
