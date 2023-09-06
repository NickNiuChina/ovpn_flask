--
-- PostgreSQL database dump
--

-- Dumped from database version 15.3
-- Dumped by pg_dump version 15.3

-- Started on 2023-09-06 10:48:03

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 16773)
-- Name: tb_user; Type: TABLE; Schema: public; Owner: ovpnflask
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


ALTER TABLE public.tb_user OWNER TO ovpnflask;

--
-- TOC entry 218 (class 1259 OID 16772)
-- Name: tb_user_user_id_seq; Type: SEQUENCE; Schema: public; Owner: ovpnflask
--

CREATE SEQUENCE public.tb_user_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tb_user_user_id_seq OWNER TO ovpnflask;

--
-- TOC entry 3344 (class 0 OID 0)
-- Dependencies: 218
-- Name: tb_user_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ovpnflask
--

ALTER SEQUENCE public.tb_user_user_id_seq OWNED BY public.tb_user.user_id;


--
-- TOC entry 3186 (class 2604 OID 16776)
-- Name: tb_user user_id; Type: DEFAULT; Schema: public; Owner: ovpnflask
--

ALTER TABLE ONLY public.tb_user ALTER COLUMN user_id SET DEFAULT nextval('public.tb_user_user_id_seq'::regclass);


--
-- TOC entry 3338 (class 0 OID 16773)
-- Dependencies: 219
-- Data for Name: tb_user; Type: TABLE DATA; Schema: public; Owner: ovpnflask
--

COPY public.tb_user (user_id, user_type, username, password, display_name, status, create_time, update_time) FROM stdin;
1	1	admin	pbkdf2:sha256:600000$FlDCDfmlKXRRkCrc$c1d8349c16ae8a02324327b0e761b47f958ea731361410274ae2fcda068a61ee	admin	1	2023-08-23 13:53:35.370594	2023-08-23 13:53:35.370594
\.


--
-- TOC entry 3345 (class 0 OID 0)
-- Dependencies: 218
-- Name: tb_user_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ovpnflask
--

SELECT pg_catalog.setval('public.tb_user_user_id_seq', 1, false);


--
-- TOC entry 3192 (class 2606 OID 16782)
-- Name: tb_user tb_user_pkey; Type: CONSTRAINT; Schema: public; Owner: ovpnflask
--

ALTER TABLE ONLY public.tb_user
    ADD CONSTRAINT tb_user_pkey PRIMARY KEY (user_id);


--
-- TOC entry 3194 (class 2606 OID 16784)
-- Name: tb_user tb_user_username_key; Type: CONSTRAINT; Schema: public; Owner: ovpnflask
--

ALTER TABLE ONLY public.tb_user
    ADD CONSTRAINT tb_user_username_key UNIQUE (username);


-- Completed on 2023-09-06 10:48:04

--
-- PostgreSQL database dump complete
--

