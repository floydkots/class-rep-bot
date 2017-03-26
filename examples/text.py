import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "class_rep_bot.settings")
django.setup()

# Import the helper gateway class
from general.AfricasTalkingGateway import AfricasTalkingGateway, AfricasTalkingGatewayException

# Specify your login credentials
username = os.environ.get("username")
apikey = os.environ.get("apikey")

# NOTE: If connecting to the sandbox, please use your sandbox login credentials

# Specify the numbers that you want to send to in a comma-separated list
# Please ensure you include the country code (+254 for Kenya)
to = "+254772489224,"
sender = "KOTS"

# And of course we want our recipients to know what we really do
message = "Floyd Kots! It's a Monday!"

# Create a new instance of our awesome gateway class
gateway = AfricasTalkingGateway(username, apikey)

# NOTE: If connecting to the sandbox, please add the sandbox flag to the constructor:
# *************************************************************************************
#             ****SANDBOX****
# gateway    = AfricasTalkingGateway(username, apiKey, "sandbox");
# **************************************************************************************

# Any gateway errors will be captured by our custom Exception class below,
# so wrap the call in a try-catch block
try:
    # Thats it, hit send and we'll take care of the rest.

    results = gateway.sendMessage(to, message, sender)

    for recipient in results:
        # status is either "Success" or "error message"
        print('number=%s;status=%s;messageId=%s;cost=%s' % (
              recipient['number'],
              recipient['status'],
              recipient['messageId'],
              recipient['cost']))

except AfricasTalkingGatewayException as e:
    print('Encountered an error while sending: %s' % str(e))
