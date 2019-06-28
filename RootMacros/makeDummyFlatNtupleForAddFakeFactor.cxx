void makeDummyFlatNtupleForAddFakeFactor(string ofile_name = "dummyFlatNtupleForAddFakeFactor.root") {
    cout << "\n========================================\n";
    cout << "Making dummy flat ntuple for addFakeFactor\n";

    // Configurations
    uint n_events = 6;
    string ttree_name = "superNt";

    // Initialize 
    TFile f(ofile_name.c_str(), "RECREATE");
    TTree t(ttree_name.c_str(), "");

    int eventNumber;    t.Branch("eventNumber", &eventNumber);
    bool isMC;          t.Branch("isMC", &isMC);
    int nSigLeps;       t.Branch("nSigLeps", &nSigLeps);
    int nInvLeps;       t.Branch("nInvLeps", &nInvLeps);
    int lep1Flav;       t.Branch("lep1Flav", &lep1Flav);
    float lep1Pt;       t.Branch("lep1Pt", &lep1Pt);
    float lep1Eta;      t.Branch("lep1Eta", &lep1Eta);
    float lep1Phi;      t.Branch("lep1Phi", &lep1Phi);
    float lep1E;        t.Branch("lep1E", &lep1E);
    int lep1q;          t.Branch("lep1q", &lep1q);
    int lep1TruthClass; t.Branch("lep1TruthClass", &lep1TruthClass);
    int lep2Flav;       t.Branch("lep2Flav", &lep2Flav);
    float lep2Pt;       t.Branch("lep2Pt", &lep2Pt);
    float lep2Eta;      t.Branch("lep2Eta", &lep2Eta);
    float lep2Phi;      t.Branch("lep2Phi", &lep2Phi);
    float lep2E;        t.Branch("lep2E", &lep2E);
    int lep2q;          t.Branch("lep2q", &lep2q);
    int lep2TruthClass; t.Branch("lep2TruthClass", &lep2TruthClass);
    int probeLep1Flav;  t.Branch("probeLep1Flav", &probeLep1Flav);
    float probeLep1Pt;  t.Branch("probeLep1Pt", &probeLep1Pt);
    float probeLep1Eta; t.Branch("probeLep1Eta", &probeLep1Eta);
    float probeLep1Phi; t.Branch("probeLep1Phi", &probeLep1Phi);
    float probeLep1E;   t.Branch("probeLep1E", &probeLep1E);
    int probeLep1q;     t.Branch("probeLep1q", &probeLep1q);
    int probeLep1TruthClass; t.Branch("probeLep1TruthClass", &probeLep1TruthClass);
    int probeLep2Flav;  t.Branch("probeLep2Flav", &probeLep2Flav);
    float probeLep2Pt;  t.Branch("probeLep2Pt", &probeLep2Pt);
    float probeLep2Eta; t.Branch("probeLep2Eta", &probeLep2Eta);
    float probeLep2Phi; t.Branch("probeLep2Phi", &probeLep2Phi);
    float probeLep2E;   t.Branch("probeLep2E", &probeLep2E);
    int probeLep2q;     t.Branch("probeLep2q", &probeLep2q);
    int probeLep2TruthClass; t.Branch("probeLep2TruthClass", &probeLep2TruthClass);

    // Fill events
    // Results assume electron (muon) fake factor = 0.5 (0.25) +/- 0.1 stat +/- 0.2 syst
    // Values that shouldn't matter
    lep1TruthClass = lep2TruthClass = (lep1Flav == 0) ? 1 : 2;
    lep1Pt = lep1Eta = lep1Phi = lep1E = 1;
    lep2Pt = lep2Eta = lep2Phi = lep2E = 1;
    probeLep1Phi = probeLep2Phi =1;
    probeLep1q = probeLep2q = 1;
        
    // Test Event 1: Get fake factor for electron in 2-lep data event
    // Result: Fake weight = 0.5 +/- 0.1 (stat) +/- 0.2 (syst)
    eventNumber = 1;
    isMC = false;
    probeLep1TruthClass = probeLep2TruthClass = 0; // Doesn't matter
    nSigLeps = 1;
    nInvLeps = 1;
    lep1Flav = lep2Flav = 1;
    probeLep1Flav = 0; // Should be opposite flavor of lep1 in dilepton events
    probeLep2Flav = lep1Flav; // Should be opposite flavor of probeLep1 in dilepton events
    probeLep1Pt = probeLep2Pt = 10;
    probeLep1Eta = probeLep2Eta = 1; // Doesn't matter
    probeLep1E = probeLep2E = 1.01*probeLep1Pt;
    lep1q = -probeLep1q; // Need opposite-sign events between probe and tag
    lep2q = probeLep1q;
    t.Fill(); 

    // Test Event 2: Get fake factor for muon in data event
    // Result: Fake weight = 0.25 +/- 0.1 (stat) +/- 0.2 (syst)
    eventNumber = 2;
    lep1Flav = 0;
    probeLep1Flav = 1;
    t.Fill(); 

    // Test Event 3: Get fake factor in underflow bin
    // Result: Fake weight = 0.25 +/- 0.1 (stat) +/- 0.2 (syst)
    eventNumber = 3;
    probeLep1Pt = 0;
    t.Fill();
    
    // Test Event 4: Get fake factor in overflow bin
    // Result: Fake weight = 0.25 +/- 0.1 (stat) +/- 0.2 (syst)
    eventNumber = 4;
    probeLep1Pt = 10E6;
    t.Fill();

    // Test Event 5: Get fake factor for double anti-ID data event
    // Result: Fake weight = -0.0625 +/- 0.05 (stat) +/- 0.1 (syst)
    eventNumber = 5;
    probeLep1Pt = 10;
    probeLep2Pt = 10;
    nSigLeps = 0;
    nInvLeps = 2;
    t.Fill();

    // Test Event 6: Reject event with incorrect lepton selection
    // Result: Fake weight = 0 +/- 0 (stat) +/- 0 (syst)
    eventNumber = 6;
    nSigLeps = 2;
    nInvLeps = 2;
    t.Fill();

    // Test Event 7: Get event weight for MC event with two prompt leptons, one ID and one anti-ID
    // Result: Fake weight = -0.25 +/- 0.1 (stat) +/- 0.2 (syst)
    eventNumber = 7;
    isMC = true;
    nSigLeps = 1;
    nInvLeps = 1;
    lep1TruthClass = lep2TruthClass = (lep1Flav == 0) ? 1 : 2;
    probeLep1TruthClass = (probeLep1Flav == 0) ? 1 : 2;
    t.Fill();
    
    // Test Event 8: Get fake factor for MC event with two prompt leptons, both anti-ID
    // Result: Fake weight = 0.0625 +/- 0.05 (stat) +/- 0.1 (syst)
    eventNumber = 8;
    nSigLeps = 0;
    nInvLeps = 2;
    probeLep2TruthClass = (probeLep2Flav == 0) ? 1 : 2;
    t.Fill();

    // Test Event 9: Get fake factor for MC event with a fake lepton
    // Result: Fake weight = 0 +/- 0 (stat) +/- 0 (syst)
    eventNumber = 9;
    probeLep2TruthClass = -1;
    t.Fill();

    // Save to file
    t.Write();
    f.Close();
    cout << "INFO :: Output file written to " << ofile_name << '\n';
    cout << "\n========================================\n\n";
}
