--
-- PostgreSQL database dump
--

-- Dumped from database version 15.3
-- Dumped by pg_dump version 15.3

-- Started on 2024-04-09 19:15:10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 843 (class 1247 OID 16403)
-- Name: clientstatus; Type: TYPE; Schema: public; Owner: mgmt
--

CREATE TYPE public.clientstatus AS ENUM (
    'offline',
    'online'
);


ALTER TYPE public.clientstatus OWNER TO mgmt;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 214 (class 1259 OID 16407)
-- Name: cnexpiredate; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.cnexpiredate (
    cn character varying(41) NOT NULL,
    releasedate timestamp without time zone,
    expiredate timestamp without time zone
);


ALTER TABLE public.cnexpiredate OWNER TO mgmt;

--
-- TOC entry 215 (class 1259 OID 16410)
-- Name: ovpnclients; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.ovpnclients (
    cn character varying(41) NOT NULL,
    ip character varying(15),
    changedate timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status integer DEFAULT 0 NOT NULL,
    storename character varying(100) DEFAULT 0 NOT NULL,
    expiredate timestamp without time zone DEFAULT '1970-01-01 00:00:00+08'::timestamp with time zone,
    releasedate timestamp without time zone DEFAULT '1970-01-01 00:00:00'::timestamp without time zone
);


ALTER TABLE public.ovpnclients OWNER TO mgmt;

--
-- TOC entry 220 (class 1259 OID 24614)
-- Name: sysconfig; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.sysconfig (
    id bigint NOT NULL,
    item character varying(100) DEFAULT 0 NOT NULL,
    ivalue character varying(100) DEFAULT 0 NOT NULL,
    catagory character varying(30) NOT NULL
);


ALTER TABLE public.sysconfig OWNER TO mgmt;

--
-- TOC entry 3382 (class 0 OID 0)
-- Dependencies: 220
-- Name: COLUMN sysconfig.catagory; Type: COMMENT; Schema: public; Owner: mgmt
--

COMMENT ON COLUMN public.sysconfig.catagory IS 'dedicated: web system config page args
global: like custom sitem global args';


--
-- TOC entry 216 (class 1259 OID 16418)
-- Name: t1; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.t1 (
    id integer NOT NULL,
    name text NOT NULL,
    age integer NOT NULL,
    address character(50),
    salary real
);


ALTER TABLE public.t1 OWNER TO mgmt;

--
-- TOC entry 219 (class 1259 OID 16440)
-- Name: tb_user; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.tb_user (
    user_id integer NOT NULL,
    user_type integer,
    username character varying(40) NOT NULL,
    password character varying(120) NOT NULL,
    display_name character varying(40) DEFAULT NULL::character varying,
    status integer DEFAULT 1 NOT NULL,
    create_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tb_user OWNER TO mgmt;

--
-- TOC entry 218 (class 1259 OID 16439)
-- Name: tb_user_user_id_seq; Type: SEQUENCE; Schema: public; Owner: mgmt
--

CREATE SEQUENCE public.tb_user_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tb_user_user_id_seq OWNER TO mgmt;

--
-- TOC entry 3383 (class 0 OID 0)
-- Dependencies: 218
-- Name: tb_user_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mgmt
--

ALTER SEQUENCE public.tb_user_user_id_seq OWNED BY public.tb_user.user_id;


--
-- TOC entry 217 (class 1259 OID 16423)
-- Name: tunovpnclients; Type: TABLE; Schema: public; Owner: mgmt
--

CREATE TABLE public.tunovpnclients (
    cn character varying(41) NOT NULL,
    ip character varying(15),
    changedate timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status integer DEFAULT 0 NOT NULL,
    storename character varying(100) DEFAULT 0 NOT NULL,
    expiredate timestamp without time zone DEFAULT '1970-01-01 00:00:00+08'::timestamp with time zone,
    releasedate timestamp without time zone DEFAULT '1970-01-01 00:00:00'::timestamp without time zone,
    url character varying(30) DEFAULT 0 NOT NULL
);


ALTER TABLE public.tunovpnclients OWNER TO mgmt;

--
-- TOC entry 3207 (class 2604 OID 16443)
-- Name: tb_user user_id; Type: DEFAULT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.tb_user ALTER COLUMN user_id SET DEFAULT nextval('public.tb_user_user_id_seq'::regclass);


--
-- TOC entry 3370 (class 0 OID 16407)
-- Dependencies: 214
-- Data for Name: cnexpiredate; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.cnexpiredate (cn, releasedate, expiredate) FROM stdin;
\.


--
-- TOC entry 3371 (class 0 OID 16410)
-- Dependencies: 215
-- Data for Name: ovpnclients; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.ovpnclients (cn, ip, changedate, status, storename, expiredate, releasedate) FROM stdin;
\.


--
-- TOC entry 3376 (class 0 OID 24614)
-- Dependencies: 220
-- Data for Name: sysconfig; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.sysconfig (id, item, ivalue, catagory) FROM stdin;
1	CUSTOMER_SITE	DEV_OVPN	dedicated
2	IP_REMOTE	service.carel-remote.com	dedicated
3	PROXY_PREFIX	RPVP	dedicated
4	DIR_APACHE_ROOT	D:\\\\software\\\\Apache-RemotePRO-server	dedicated
5	DIR_APACHE_SUB	conf\\\\extra	dedicated
6	IP_PORT	443	dedicated
7	DIR_VPN_SCRIPT	vpntool	dedicated
8	DIR_TUN	tun-ovpn-files	dedicated
9	DIR_TAP	tap-ovpn-files	dedicated
10	DIR_EASYRSA	easyrsa	dedicated
11	DIR_GENERIC_CLIENT	generic-ovpn	dedicated
12	DIR_REQ	reqs	dedicated
13	DIR_REQ_DONE	reqs-done	dedicated
14	DIR_VALIDATED	validated	dedicated
\.


--
-- TOC entry 3372 (class 0 OID 16418)
-- Dependencies: 216
-- Data for Name: t1; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.t1 (id, name, age, address, salary) FROM stdin;
\.


--
-- TOC entry 3375 (class 0 OID 16440)
-- Dependencies: 219
-- Data for Name: tb_user; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.tb_user (user_id, user_type, username, password, display_name, status, create_time, update_time) FROM stdin;
1	1	super	pbkdf2:sha256:600000$0H5yhhn7uVEjJmHx$3032a65104b01f2021b9fb30a55a39a521d18f596ae7c1ca01340ea0a0815480	super	1	2023-08-26 17:27:02.880914	2023-08-26 17:27:02.880914
3	2	user	pbkdf2:sha256:600000$SgnKKgwaetGADFhF$e08a6df4cbef6847091ca8a01bce36dd2c761603235ecd840afac5f84c4aa855	user	1	2023-08-26 00:54:24.214524	2024-04-09 18:22:53
2	1	admin	pbkdf2:sha256:600000$A1iWQjT7ZKUJEmcE$974a85ae252430be890481719559573fd4cd7e0eb4d42e641cfc133c01da043b	admin	1	2023-08-23 20:54:00.600386	2024-04-09 18:22:56
\.


--
-- TOC entry 3373 (class 0 OID 16423)
-- Dependencies: 217
-- Data for Name: tunovpnclients; Type: TABLE DATA; Schema: public; Owner: mgmt
--

COPY public.tunovpnclients (cn, ip, changedate, status, storename, expiredate, releasedate, url) FROM stdin;
boss-830f8af0-c498-11ed-a230-c400addfed82	192.168.80.102	2023-05-16 16:55:13	1	奥乐齐北外滩莱福士店4	2033-03-14 09:01:12	1970-01-01 00:00:00	9802078158494-0xc0a85066
boss-830f8af0-c498-11ed-a230-c400addfed83	192.168.80.103	2023-05-01 16:55:13	1	奥乐齐北外滩莱福士店5	2033-03-14 18:51:02	1970-01-01 00:00:00	2198219821949-0xc0a85067
boss-830f8af0-c498-11ed-a230-c400addfed79	192.168.80.98	2023-04-11 06:55:13	1	奥乐齐北外滩莱福士店1	2033-04-14 09:51:02	1970-01-01 00:00:00	5760256039884-0xc0a85062
boss-830f8af0-c498-11ed-a230-c400addfed78	192.168.80.97	2023-05-11 06:55:13	1	111111111111111111111111111111111	2033-03-14 09:51:02	1970-01-01 00:00:00	2579197724980-0xc0a85061
boss-830f8af0-c498-11ed-a230-c400addfed85	192.168.80.105	2023-01-01 06:55:13	1	奥乐齐北外滩莱福士店7	2033-06-14 09:51:02	1970-01-01 00:00:00	7717845325527-0xc0a85069
boss-830f8af0-c498-11ed-a230-c400addfed84	192.168.80.104	2023-02-21 06:55:13	1	11111111111	2033-03-04 09:51:02	1970-01-01 00:00:00	7307141349259-0xc0a85068
boss-830f8af0-c498-11ed-a230-c400addfed80	192.168.80.99	2023-05-18 06:55:13	1	22222222222222222	2033-03-15 09:51:02	1970-01-01 00:00:00	8503385463569-0xc0a85063
boss-830f8af0-c498-11ed-a230-c400addfed81	192.168.80.101	2023-05-21 06:55:13	1	33333333333333	2033-03-19 09:51:02	1970-01-01 00:00:00	4755240208903-0xc0a85065
boss-830f8af0-c498-11ed-a230-c400addfed86	192.168.80.106	2023-06-21 06:55:13	0	4444444444444444	2033-01-19 09:51:02	1970-01-01 00:00:00	8206036719928-0xc0a8506a
boss-830f8af0-c498-11ed-a230-c400addfed88	192.168.80.107	2023-06-11 06:55:13	0	55555555555555555	2033-03-24 09:51:02	1970-01-01 00:00:00	9272278248651-0xc0a8506b
\.


--
-- TOC entry 3384 (class 0 OID 0)
-- Dependencies: 218
-- Name: tb_user_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mgmt
--

SELECT pg_catalog.setval('public.tb_user_user_id_seq', 1, false);


--
-- TOC entry 3215 (class 2606 OID 16432)
-- Name: cnexpiredate cnexpiredate_pk; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.cnexpiredate
    ADD CONSTRAINT cnexpiredate_pk PRIMARY KEY (cn);


--
-- TOC entry 3217 (class 2606 OID 16434)
-- Name: ovpnclients ovpnclients_un; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.ovpnclients
    ADD CONSTRAINT ovpnclients_un UNIQUE (cn);


--
-- TOC entry 3227 (class 2606 OID 24620)
-- Name: sysconfig sysconfig_pkey; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.sysconfig
    ADD CONSTRAINT sysconfig_pkey PRIMARY KEY (id);


--
-- TOC entry 3219 (class 2606 OID 16436)
-- Name: t1 t1_pkey; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.t1
    ADD CONSTRAINT t1_pkey PRIMARY KEY (id);


--
-- TOC entry 3223 (class 2606 OID 16449)
-- Name: tb_user tb_user_pkey; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.tb_user
    ADD CONSTRAINT tb_user_pkey PRIMARY KEY (user_id);


--
-- TOC entry 3225 (class 2606 OID 16451)
-- Name: tb_user tb_user_username_key; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.tb_user
    ADD CONSTRAINT tb_user_username_key UNIQUE (username);


--
-- TOC entry 3221 (class 2606 OID 16438)
-- Name: tunovpnclients tunovpnclients_cn_key; Type: CONSTRAINT; Schema: public; Owner: mgmt
--

ALTER TABLE ONLY public.tunovpnclients
    ADD CONSTRAINT tunovpnclients_cn_key UNIQUE (cn);


-- Completed on 2024-04-09 19:15:10

--
-- PostgreSQL database dump complete
--

