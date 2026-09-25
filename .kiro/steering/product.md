---
inclusion: always
---

# TechConf: dominio e perimetro

TechConf gestisce utenti, conferenze tecniche e iscrizioni. Il progetto segue la
traccia `Exam/Exam.MD`; i contratti in `contracts/openapi/` definiscono le interfacce.

I tre servizi obbligatori sono:
- `user-service`: anagrafica partecipanti, speaker e organizzatori; email univoca
  senza distinzione tra maiuscole e minuscole.
- `event-service`: eventi, organizzatore valido, date, capienza, prezzo e ciclo
  `draft -> published -> cancelled`, con le sole transizioni ammesse dalla traccia.
- `registration-service`: verifica utente ed evento via HTTP, iscrizione a eventi
  pubblicati, prezzo acquisito dall'evento, unicità delle iscrizioni confermate,
  limite di capienza, cancellazione con posto liberato e statistiche.

Dipendenze: event chiama user; registration chiama direttamente user ed event.
Ogni servizio possiede i propri dati. Non condivide database o oggetti in memoria
con gli altri servizi.

Feedback e notifiche sono bonus successivi ai tre obbligatori, da affrontare solo
se inclusi nella fase autorizzata. Non aggiungere frontend, autenticazione,
pagamenti, invio reale di email/SMS, cloud, container o DBMS esterni: non fanno
parte del perimetro richiesto.

Il risultato comprende specifiche tracciabili, codice, test, cronologia Git e
documentazione dei bug. Il solo superamento del collaudo non esaurisce i requisiti.
Sviluppare soltanto la fase richiesta nella sessione, senza anticipare quelle successive.
