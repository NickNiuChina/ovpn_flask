Translations:
    Config: babel.cfg
    
    Steps:
        extract strings: 
            pybabel extract -F babel.cfg -o myproject/translations/messages.pot .

        create translation
            pybabel init -i myproject/translations/messages.pot -d translations -l zh

        compile the translations
            pybabel compile -d myproject/translations

        **********
        strings change, merge change
            pybabel update -i myproject/translations/messages.pot -d myproject/translations

            pybabel compile -d myproject/translations

1. client exipre date ------ Done
openssl x509 -enddate -noout -in /opt/easyrsa-all/pki/issued/boss-fa09b494-4902-11ed-9561-c400ad6b7bab.crt

2. if validate cert
Req validate:
cat /opt/reqs-done/f3faeb3c-e60a-11ec-a425-000a5c81dcf9.req | tail -n +3  |  openssl x509 -noout

3. Update log info, add client ip etc. 

