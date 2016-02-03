var measures = [
    {
        chartId: 'rosuvastatin',
        chartName: 'Rosuvastatin Calcium vs. Atorvastatin',
        chartIntro: 'Prescribing of <a href="/chemical/0212000AA">Rosuvastatin Calcium (BNF code 0212000AA)</a>, compared with <a href="/chemical/0212000B0">Atorvastatin (BNF code 0212000B0)</a>.',
        chartDescription: 'Statins are the most commonly prescribed class of drug in the UK. Atorvastatin and Rosuvastatin are members of this class, and are both high-potency statins. There will always be reasons why occasional patients do better with a particular drug, but overall there is no good evidence that Rosuvastatin is better than atorvastatin. It is, however, vastly more expensive. When atorvastatin came off patent, and became cheap, practices tended to switch people away from expensive Rosuvastatin.',
        numIds: [{ id: '0212000AA', 'name': 'Rosuvastatin'}],
        denomIds: [{ id: '0212000B0', 'name': 'Atorvastatin'}]
    },
    {
        chartId: 'cerazette',
        chartName: 'Cerazette vs. Desogesterel',
        chartIntro: 'Prescribing of branded Cerazette (BNF code 0703021Q0BB) compared with prescribing of <a href="/chemical/0703021Q0">all Desogesterel (BNF code 0703021Q0)</a>.',
        chartDescription: 'This is the NHS Business Service Authority\'s top cost-saver from generic switching. Cerazette and desogestrel are both exactly the same drug, the same molecule, but Cerazette is an expensive branded package, and desogestrel is a cheap generic package.',
        numIds: [{ id: '0703021Q0BB', 'name': 'Cerazette'}],
        denomIds: [{ id: '0703021Q0', 'name': 'Desogestrel'}]
    },
    {
        chartId: 'cephalosporins',
        chartName: 'Cephalosporins per oral antibiotics STAR-PU',
        chartIntro: 'Prescribing of <a href="/bnf/050102">Cephalosporins (BNF section 5.1.2)</a> compared with item-based STAR-PUs for oral antibiotics.',
        chartDescription: 'Cephalosporins are broad spectrum antibiotics which can be used when others have failed. It is important that they are used sparingly, to avoid drug-resistant bacteria developing. This measure looks at the quantity of cephalosporins prescribed per head of population, corrected for the age and sex distribution of that population.',
        numIds: [{ id: '050102', 'name': 'Cephalosporins and other Beta-Lactams'}],
        denom: 'star_pu_oral_antibac_items',
        denomIds: []
    },
    {
        chartId: 'antibiotics',
        chartName: 'All antibacterial drugs per oral antibiotics STAR-PU',
        chartIntro: 'Prescribing of <a href="/bnf/0501">Antibacterial Drugs (BNF section 5.1)</a> compared with item-based STAR-PUs for oral antibiotics.',
        chartDescription: 'It is important that we don\'t overuse antibiotics. This shows how many are being prescribed locally.',
        numIds: [{ id: '0501', 'name': 'Antibacterial Drugs'}],
        denom: 'star_pu_oral_antibac_items',
        denomIds: []
    },
    {
        chartId: 'pioglitazone',
        chartName: 'Pioglitazone Hydrochloride vs. all Antidiabetic Drugs',
        chartIntro: 'Prescribing of <a href="/chemical/0601023B0">Pioglitazone Hydrochloride (BNF code 0601023B0)</a> compared with prescribing of all <a href="/bnf/060102">Antidiabetic Drugs</a> (BNF code 6.1.2).',
        chartDescription: 'Rosiglitazone is an antidiabetic drug that turned out to increase the risk of heart problems, and was effectively withdrawn from the market. There is concern that the problems may have been a "class effect", covering other related drugs, and so doctors have tended to also stop using pioglitazone. This shows how local practice reflects that national trend.',
        numIds: [{ id: '0601023B0', 'name': 'Pioglitazone Hydrochloride'}],
        denomIds: [{ id: '060102', 'name': 'All diabetes'}]
    },
    {
        chartId: 'celecoxib',
        chartName: 'Celecoxib vs. all NSAIDs',
        chartIntro: 'Prescribing of <a href="/chemical/0801050AY">Celecoxib (BNF code 0801050AY)</a> and <a href="/chemical/1001010AH">Celecoxib (BNF code 1001010AH)</a> compared with prescribing of all <a href="/bnf/100101">Non-Steroidal Anti-Inflammatory Drugs</a> (BNF section 1.1.1).',
        chartDescription: 'Coxib drugs are an interesting illustration of a common phenomenon in medicine: the need to make a trade off between risk and benefit, in different patients. Long term use of NSAID painkillers puts patients at increased risk of gastric bleeds. Coxib painkillers are effective at treating pain, with lower risk of bleeding; but they are much more expensive, and come with a higher risk of cardiovascular problems. Overall, therefore, they are sensible to use in some patients, but if one area is prescribing a lot of coxibs (or very few) then that may mean that they have unusual patients, or it may mean that doctors\' thresholds for using them are different to their colleagues nationally.',
        numIds: [{ id: '0801050AY', 'name': 'Celecoxib'}, {id: '1001010AH', 'name': 'Celecoxib'}],
        denomIds: [{ id: '100101', 'name': 'Non-Steroidal Anti-Inflammatory Drugs'}]
    }
];
module.exports = measures;
