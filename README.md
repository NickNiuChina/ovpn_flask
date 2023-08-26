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

  