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