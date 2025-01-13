Translations:
    Config: babel.cfg
    
    Steps:
        extract strings: 
            pybabel extract -F babel.cfg -o myproject/messages.pot.

        create translation
            pybabel init -i myproject/messages.pot -d translations -l zh

        compile the translations
            pybabel compile -d myproject/translations

        **********
        strings change, merge change
            pybabel update -i myproject/messages.pot -d myproject/translations