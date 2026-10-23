machine name-- ""
machine no -- ""
two stringvars need to add in the admin settings..

three frames
1. dummy id
2. pack id
3. bmm cmb id

for each frame..
1. api url- (stringvar)
2. api key- (stringvar)
3. machine name- (stringvar)
4. machine number- (stringvar)

toggle button for each frame which validates (api url + api key)

No—don’t add  ?x_api_key=my_api_key  to the URL. The server expects the key in the  X-API-Key  request header, which the application already sends when it validates a key.

Use the endpoint URL only, for example  http://<server-host>:8001/data/dummy  (or  /data/packid  or  /data/bmbcmb ). The entered key must exactly match the server key for that endpoint. If it still reports “missing or wrong API key,” check that the URL points to the correct endpoint and that the running server is using the expected keys and code.
