void makeDummyFakeFactor(string ofile_name = "fakeFactorDummy.root", float nom_mu_val = 0.5, float nom_el_val = 0.60) {
    cout << "\n========================================\n";
    cout << "Making dummy fake factors\n";
    // Configurations
    float stat_unc = 0.1;
    float sys_unc = 0.2;

    int nbins = 1;
    float xmin = 3;
    float xmax = 100;

    int nbinsy = 1;
    float ymin = 0;
    float ymax = 3.2;

    // Create file and histograms
    TFile *f = new TFile(ofile_name.c_str(), "RECREATE");
    //TH1D h_mu("FakeFactor_mu_pt","", nbins, xmin, xmax);
    //TH1D h_mu_syst("FakeFactor_mu_pt__Syst","", nbins, xmin, xmax);
    //TH1D h_el("FakeFactor_el_pt","", nbins, xmin, xmax);
    //TH1D h_el_syst("FakeFactor_el_pt__Syst","", nbins, xmin, xmax);

    TH2D h_mu("FakeFactor2D_mu_pt_eta","", nbins, xmin, xmax, nbinsy, ymin, ymax);
    TH2D h_mu_syst("FakeFactor2D_mu_pt_eta__Syst","", nbins, xmin, xmax, nbinsy, ymin, ymax);
    TH2D h_el("FakeFactor2D_el_pt_eta","", nbins, xmin, xmax, nbinsy, ymin, ymax);
    TH2D h_el_syst("FakeFactor2D_el_pt_eta__Syst","", nbins, xmin, xmax, nbinsy, ymin, ymax);
    // Set histograms
    h_mu.SetBinContent(1,1, nom_mu_val);
    h_mu.SetBinError(1,1, stat_unc);
    h_mu_syst.SetBinContent(1,1, sys_unc);
    h_mu_syst.SetBinError(1,1, 0);

    h_el.SetBinContent(1,1, nom_el_val);
    h_el.SetBinError(1,1, stat_unc);
    h_el_syst.SetBinContent(1,1, sys_unc);
    h_el_syst.SetBinError(1,1, 0);

    // Save histograms to file
    f->Write();
    cout << "INFO :: Output file written to " << ofile_name << '\n';
    f->Close();
    cout << "\n========================================\n\n";
}
