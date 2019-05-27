
def transform_incoming_message(source, message):
    if source == 'external' and message['type'] == 'bbo':
        message['type'] = 'external_feed_change'
        message['e_best_bid'] = message['best_bid']   
        message['e_best_offer'] = message['best_offer']
    if source == 'external' and message['type'] == 'signed_volume':
        message['type'] = 'external_feed_change'
        message['e_signed_volume'] = message['signed_volume']
    return message

