OVPN Management private project. Based on Python Flask.

1. Deployment
    1. Install Python and venv
    2. Prepare database
    3. Install nginx and config

2. Configuration
  Set environment to indicate which server the application runs on:

  - Powershell: 

    $evn:CURRENT_SERVSER='CAREL_OVPN'

    $evn:CURRENT_SERVSER

    dir env

  - CMD: 

    set CURRENT_SERVSER=CAREL_OVPN

    echo %CURRENT_SERVSER%

  - Linux:

    export CURRENT_SERVSER=CAREL_OVPN

    echo $CURRENT_SERVSER

  3. Boss URL
  - URL
    len("RVRP@9801456451909-0xc0a8788a@") - 30

    # 添加url列
    ALTER TABLE IF EXISTS public.tunovpnclients
    ADD COLUMN url character varying(30) NOT NULL DEFAULT 0;

  4. Database
    1. backup to plain files
    2. Restore:
    psql -U mgmt mgmtdb < schema.sql

  