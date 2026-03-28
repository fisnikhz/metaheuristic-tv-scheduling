<table border="0">
 <tr>
    <td><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/University_of_Prishtina_logo.svg/1200px-University_of_Prishtina_logo.svg.png" width="150" alt="University Logo" /></td>
    <td>
      <p>Universiteti i Prishtinës</p>
      <p>Fakulteti i Inxhinierisë Elektrike dhe Kompjuterike</p>
      <p>Inxhinieri Kompjuterike dhe Softuerike - Programi Master</p>
      <p>Profesor: Prof. Dr. Kadri Sylejmani</p>
      <p>Asistent: MSc. Labeat Arbneshi</p>
    </td>
 </tr>
</table>


## Përshkrimi i Projektit: Optimizimi i Orarit Televiziv

Ky projekt adreson **Problemin e Planifikimit Televiziv për Hapësira Publike** (TV Channel Scheduling Optimization for Public Spaces) në kuadër të lëndës **Algoritmet e Avancuara**. Objektivi primar është përzgjedhja dhe planifikimi optimal i një nënbashkësie të programeve televizive në kanale të shumta, me qëllim maksimizimin e pikëve totale të shikueshmërisë.

**Kufizimet dhe Qëllimet Kryesore:**

Përveç kufizimeve bazë kohore, problemi përfshin rregulla specifike për të siguruar një përvojë cilësore shikimi:

*   **Time Window Constraint:** Programet duhet të planifikohen strikt brenda intervalit kohor global të përcaktuar (Hapja dhe Mbyllja).
*   **No Overlap Constraint:** Ndalohet rreptësisht mbivendosja kohore e programeve në të njëjtin kanal.
*   **Minimum Duration:** Programet duhet të kenë një kohëzgjatje minimale për t'u konsideruar të vlefshme.
*   **Genre Repetition:** Për të siguruar shumëllojshmëri, ka një kufizim në numrin e programeve të njëpasnjëshme të të njëjtit zhanër.
*   **Priority Blocks:** Blloqe kohore specifike ku vetëm kanale të caktuara kanë prioritet ose lejohen të transmetojnë.
*   **Time Preferences:** Bonuse pikësh për transmetimin e zhanreve të caktuara në orare të preferuara.
*   **Optimization Goal:** Maksimizimi i funksionit objektiv, duke balancuar pikët e programeve me penalitetet e mundshme.

## Beam Search Scheduler

 **Beam Search Scheduler**, është një algoritëm **deterministik** që tejkalon kufizimet e qasjeve standarde **Greedy** përmes eksplorimit paralel të hapësirës së zgjidhjeve.

**Metodologjia:**

1.  **Beam Search Strategy:** Në vend të ndjekjes së një rruge të vetme, algoritmi mirëmban një bashkësi prej $N$ zgjidhjesh të pjesshme më premtuese në çdo hap (**Beam Width**). Kjo mundëson shmangien e minimumeve lokale dhe rikuperimin nga vendimet sub-optimale të hershme.
2.  **Lookahead Mechanism:** Përtej vlerësimit të menjëhershëm, algoritmi implementon një mekanizëm **Lookahead** me thellësi të konfiguruar. Kjo analizon impaktin e vendimeve aktuale në mundësitë e ardhshme, duke parandaluar bllokimin e programeve me vlerë të lartë.
3.  **Density Heuristic:** Për vlerësimin e potencialit të intervaleve kohore të mbetura, përdoret një heuristikë e bazuar në dendësinë e pikëve (pikë/minutë).

**Konfigurimi i Parametrave:**
*   **Beam Width:** 100. Ruan 100 degëzimet më të mira të pemës së kërkimit në çdo iteracion.
*   **Lookahead:** 4 hapa. Vlerëson pasojat e vendimeve deri në 4 nivele thellësi.
*   **Density Percentile:** Fokusohet në 25% të programeve më të mira për vlerësim heuristik)

Ky kombinim i eksplorimit **Beam Search** dhe heuristikave të avancuara **Lookahead** mundëson gjetjen e zgjidhjeve të cilësisë së lartë në mënyrë efikase.

## Optimizuesi Simulated Annealing

Për të përmirësuar më tej orarin, ne kemi implementuar një metaheuristikë **Simulated Annealing (SA)**. Ky optimizim ekzekutohet **mbi zgjidhjen fillestare të gjeneruar nga inicializimi me Beam Search**, duke e përdorur atë si një pikënisje të fortë në vend që të fillojë nga e para.

**Metodologjia:**

1.  **Zgjidhja Fillestare:** Algoritmi fillon me orarin e plotë dhe të vlefshëm të gjeneruar nga faza e Beam Search.
2.  **Operatorët e Fqinjësisë (Neighborhood):** SA eksploron hapësirën e zgjidhjeve në mënyrë të përsëritur duke përdorur operatorë të shumtë të perturbimit (p.sh., heqja e blloqeve të programeve të planifikuara, ndërrimi i kanaleve).
3.  **Strategjia e Rikonstruktimit:** Pasi një zgjidhje të jetë ngacmuar (perturbuar), përdoret një mekanizëm i lokalizuar rikonstruktimi për të mbushur hapësirat e lira me programe me vlerë më të lartë, duke ruajtur në të njëjtën kohë të gjitha kufizimet strikte.
4.  **Skeda Adaptive e Ftohjes:** Algoritmi pranon zgjidhjet që përmirësojnë, si dhe ato që përkeqësojnë gjendjen, bazuar në kriterin e Metropolis për t'i shpëtuar optimumeve lokale. Temperatura fillestare dhe shpejtësia e ftohjes përshtaten në mënyrë dinamike me madhësisë e problemit.

## Ekzekutimi i Projektit

Për të ekzekutuar algoritmin me Simulated Annealing, përdorni argumentin `--input` duke specifikuar fajllin hyrës:

```bash
python main.py --input data/input/australia.json
```

Mund të specifikoni numrin e iterimeve për SA (default është 5000):
```bash
python main.py --input data/input/australia.json --iterations 10000
```

Algoritmi do të fillojë ekzekutimin (fillimisht me Beam Search pastaj me SA) dhe në fund do të ruajë rezultatin në folderin `data/output/`.
