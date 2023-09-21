#!/bin/bash

# Generate openvpn generic client files for route or PC
# Released on Aug/28/2023 nick.niu@carel.com

#/opt/tun-ovpn-files
# easyrsa
# easyrsa-all
# generic-ovpn
# reqs
# reqs-done
# validated

# bash /opt/ovpn_flask/vpntool/generate-generic-client-cert.sh /opt/tun-ovpn-files cn dev tun-ovpn-files

# check arguments count
if [ "$#" -ne 4 ]; then
    echo "FATAL ERROR: ARGUMENTS COUNT IS NOT CORRECT"
    exit 5
fi

# OVPN main directory
OVPN_DIR=$1
# OVPN cn
CN=$2

# CS: for oss backup dir
# shield dev carel or sgovpn
CS=$3

FILES_DIR=$4
# dir: tun-ovpn-files or tap-ovpn-files currently

# check relative dirs
if ! [[ -d $OVPN_DIR  ]];then
    echo "FATAL ERROR: OVPN_DIR DOES NOT EXIST"
    exit 5
fi

# Tools and dirs

export OPENSSL=/usr/bin/openssl
export EASYRSACMD="${OVPN_DIR}/easyrsa/easyrsa"

export REQDIR="${OVPN_DIR}/reqs"

export BACKUPDIR="${OVPN_DIR}/easyrsa-all"
export TOOLDIR="${OVPN_DIR}/easyrsa"
export REQDIR="${OVPN_DIR}reqs"
export REQDONEDIR="${OVPN_DIR}/reqs-done"

if ! [[ -r ${OPENSSL} ]]; then
    echo "FATAL ERROR: CHECK OPENSSL LAMBDA LAYER"
    exit 5
fi
if ! [[ -r ${EASYRSACMD} ]]; then
    echo "FATAL ERROR: CHECK EASYRSA LAMBDA LAYER"
    exit 5
fi

# Ensure the workdir is a tmp dir in case any failure occurs
export WORKDIR=$(mktemp -d -p /tmp)
cd $WORKDIR

# Downloading files needed
echo "Downloading files....:"
cp -r $TOOLDIR/* $WORKDIR
mkdir -p ${WORKDIR}/${CN}

echo "Free Space in Lambda Temp Dir:"
df -h $WORKDIR

# check Templates, later on this will be updated to seprated server and fetch from ovpnserver.
echo "Checking OpenVPN Templates presence"
CABUNDLE=$WORKDIR/pki/ca.crt
TA=$WORKDIR/ta.key
for f in $CABUNDLE $TA; do
    if ! [[ -r $f ]]; then
        echo "FATAL ERROR: $f not readable"
        cd && rm -rf $WORKDIR
        exit
    fi
done

for p in udp tcp; do
    OVPN_T_header=$WORKDIR/clienttemplates/template-$p.header
    OVPN_T_footer=$WORKDIR/clienttemplates/template-$p.footer
    for f in $OVPN_T_header $OVPN_T_footer; do
        if ! [[ -r $f ]]; then
            echo "FATAL ERROR: $f not readable"
            cd && rm -rf $WORKDIR
            exit
        fi
    done
done


#############################################################
# CERTIFICATE GENERATION
#############################################################

client_crt=${BACKUPDIR}/pki/issued/$CN.crt
client_key=${BACKUPDIR}/pki/private/$CN.key

if [[ -r $client_key ]] && [[ -r $client_crt ]]; then
    echo "FATAL ERROR: Certificate for $CN already exists!"
    exit 10
else
    echo "Generating new certificate for $DEVICE_UUID with CN=$CN"
    ${OPENSSL} rand -writerand $WORKDIR/pki/.rnd
    set +e
    output=$(EASYRSA_OPENSSL=${OPENSSL} bash ${EASYRSACMD} --vars=pki/vars build-client-full $CN nopass)
    result=$?
    set -e
    if [[ $result -ne 0 ]]; then
        echo "FATAL ERROR: EasyRSA build-client-full failed for $CN:"
        echo "$output"
        cd && rm -rf $WORKDIR
        exit
    fi
fi


#############################################################
# OPENVPN PROFILES GENERATION
#############################################################

echo "Generating OpenVPN Profiles for $CN"
client_crt=${WORKDIR}/pki/issued/$CN.crt
client_key=${WORKDIR}/pki/private/$CN.key

for p in udp tcp; do
    OVPN_T_header=$WORKDIR/clienttemplates/template-$p.header
    OVPN_T_footer=$WORKDIR/clienttemplates/template-$p.footer
    OVPN=${WORKDIR}/${CN}.conf
    cat $OVPN_T_header > $OVPN
    echo >> $OVPN
    echo "<ca>" >> $OVPN
    cat $CABUNDLE >> $OVPN
    echo "</ca>" >> $OVPN
    echo "<cert>" >> $OVPN
    ${OPENSSL} x509 -in $client_crt >>$OVPN
    echo "</cert>" >> $OVPN
    echo "<key>" >> $OVPN
    cat $client_key >> $OVPN
    echo "</key>" >> $OVPN
    echo "key-direction 1" >> $OVPN
    echo "<tls-auth>" >> $OVPN
    cat $TA >> $OVPN
    echo "</tls-auth>" >> $OVPN
    echo >> $OVPN
    cat $OVPN_T_footer >> $OVPN
done



#############################################################
# OPENVPN PROFILES ARCHIVE BUNDLE
#############################################################

echo "Generating OpenVPN ZIP FILE for $CN"

TARGET=${WORKDIR}/${CN}

cp -fv ${WORKDIR}/ta.key ${WORKDIR}/${CN}/
cp -fv ${WORKDIR}/pki/ca.crt ${WORKDIR}/${CN}/
cp -fv ${WORKDIR}/pki/private/$CN.key ${WORKDIR}/${CN}/
cp -fv ${WORKDIR}/pki/issued/$CN.crt ${WORKDIR}/${CN}/
cp -fv ${OVPN} ${WORKDIR}/${CN}/

zip -r $CN.zip $CN

#############################################################
# OPENVPN PROFILES ENCRYPTION
#############################################################


echo "Free Space in Lambda Temp Dir:"
df -h $WORKDIR


#############################################################
# OSS STORE UPDATE
#############################################################

export OSSUTIL=/usr/local/bin/ossutil64
if ! [[ -r ${OSSUTIL} ]]; then
    echo "FATAL ERROR: CHECK OPENSSL LAMBDA LAYER"
    exit 5
fi

# Save the req cert key files for new clients
echo "Backup client req,key,crt files "
cp -fv $WORKDIR/pki/reqs/${CN}.req $BACKUPDIR/pki/reqs/
cp -fv $WORKDIR/pki/private/${CN}.key $BACKUPDIR/pki/private/
cp -fv $WORKDIR/pki/issued/${CN}.crt $BACKUPDIR/pki/issued/
cp -fv $WORKDIR/pki/certs_by_serial/*.pem $BACKUPDIR/pki/certs_by_serial/
cp -fv $WORKDIR/${CN}.zip "${OVPN_DIR}/generic-ovpn/"

for FILE in $WORKDIR/pki/reqs/*.req; do
    ossutil64 cp $FILE oss://carelvpn/${CS}/${FILES_DIR}/easyrsa-tcp/pki/reqs/ -f
done

for FILE in $WORKDIR/pki/private/*.key; do
    ossutil64 cp -f $FILE oss://carelvpn/${CS}/${FILES_DIR}/easyrsa-tcp/pki/private/ -f
done

for FILE in $WORKDIR/pki/issued/*.crt; do
    ossutil64 cp -f $FILE oss://carelvpn/${CS}/${FILES_DIR}/easyrsa-tcp/pki/issued/ -f
done

for FILE in $WORKDIR/pki/certs_by_serial/*.pem; do
    ossutil64 cp -f $FILE oss://carelvpn/${CS}/${FILES_DIR}/easyrsa-tcp/pki/certs_by_serial/ -f
done

ossutil64 cp -f $WORKDIR/${CN}.zip oss://carelvpn/${CS}/${FILES_DIR}/generic-ovpn/ -f


# Update OSS store
echo "Updating OSS store"
cd $WORKDIR

cd && rm -rf $WORKDIR

echo "SELFDEFINEDSUCCESS"; # This will tell the upload process is tatolly successlly