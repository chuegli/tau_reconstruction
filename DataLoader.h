#include "TauTuple.h"
#include "TROOT.h"
#include "TLorentzVector.h"
#include "Math/Vector4D.h"

using namespace ROOT::Math;

std::shared_ptr<TFile> OpenRootFile(const std::string& file_name){
    std::shared_ptr<TFile> file(TFile::Open(file_name.c_str(), "READ"));
    if(!file || file->IsZombie())
        throw std::runtime_error("File not opened.");
    return file;
}


struct Data {
    Data(size_t nx, size_t ny, size_t nz) : x(nx, 0), y(ny, 0), z(nz, 0){ }
    std::vector<float> x, y, z;
};

// List of features:
enum class Feature {
    pfCand_pt                   = 0,
    pfCand_eta                  = 1,
    pfCand_phi                  = 2,
    pfCand_mass                 = 3,
    pfCand_pdgId                = 4,
    pfCand_charge               = 5,
    pfCand_pvAssociationQuality = 6,
    pfCand_fromPV               = 7,
    pfCand_puppiWeight          = 8, 
    pfCand_puppiWeightNoLep     = 9,
    pfCand_lostInnerHits        = 10,
    pfCand_numberOfPixelHits    = 11,
    pfCand_numberOfHits         = 12,
    pfCand_hasTrackDetails      = 13,
    pfCand_dxy                  = 14,
    pfCand_dxy_error            = 15,
    pfCand_dz                   = 16,
    pfCand_dz_error             = 17,
    pfCand_track_chi2           = 18,
    pfCand_track_ndof           = 19,
    pfCand_caloFraction         = 20,
    pfCand_hcalFraction         = 21,
    pfCand_rawCaloFraction      = 22,
    pfCand_rawHcalFraction      = 23,
    pfCand_valid                = 24,
    pfCand_px                   = 25,
    pfCand_py                   = 26,
    pfCand_pz                   = 27,
    pfCand_E                    = 28,
};

string feature_names[29] = {"pfCand_pt", "pfCand_eta", "pfCand_phi", "pfCand_mass", "pfCand_pdgId", "pfCand_charge", 
    "pfCand_pvAssociationQuality", "pfCand_fromPV", "pfCand_puppiWeight", "pfCand_puppiWeightNoLep", "pfCand_lostInnerHits", 
    "pfCand_numberOfPixelHits", "pfCand_numberOfHits", "pfCand_hasTrackDetails", "pfCand_dxy", "pfCand_dxy_error", "pfCand_dz", 
    "pfCand_dz_error", "pfCand_track_chi2", "pfCand_track_ndof", "pfCand_caloFraction", "pfCand_hcalFraction", 
    "pfCand_rawCaloFraction", "pfCand_rawHcalFraction","pfCand_valid ","pfCand_px","pfCand_py ","pfCand_pz ","pfCand_E "};

struct DataLoader {

    //This is the constructor:
    DataLoader(std::string file_name, size_t _n_tau, Long64_t _start_dataset, Long64_t _end_dataset) :
        file(OpenRootFile(file_name)), tuple(file.get(), true), n_tau(_n_tau), current_entry(_start_dataset), start_dataset(_start_dataset), end_dataset(_end_dataset){}
 
    std::shared_ptr<TFile> file;
    tau_tuple::TauTuple tuple; // tuple is the tree
    size_t n_tau; // number of events(=taus)
    Long64_t start_dataset;
    Long64_t end_dataset;
    Long64_t current_entry; // number of the current entry

    static const size_t n_pf    = 100; // number of pf candidates per event
    static const size_t n_fe    = 29;  // number of featurese per pf candidate
    static const size_t n_count = 2;   // chanrged and neutral particle count

    // Creation of map of features:
    std::map<std::string, int> MapCreation(){
        std::map<std::string, int> mapOfFeatures;
        for(size_t i = 0; i <= 28; ++i){
            mapOfFeatures[feature_names[i]] = i;
        }
        return mapOfFeatures;
    }

    bool HasNext() {     
        return (current_entry + n_tau) <= end_dataset;
    }
    Data LoadNext(){
        Data data(n_tau * n_pf * n_fe, n_tau * n_count, n_tau); // Creates an empty data structure

        for(size_t tau_ind = 0; tau_ind < n_tau; ++tau_ind, ++current_entry) { 
            tuple.GetEntry(current_entry); // get the entry of the current event
            const tau_tuple::Tau& tau = tuple(); // tau is out tree

            data.z.at(tau_ind) = tau.tau_decayModeFindingNewDMs ? tau.tau_decayMode : -1; // end is the else
            // Fill the labels:
            auto get_y = [&](size_t count_ind) -> float& {
                size_t index = GetIndex_y(tau_ind, count_ind);
                return data.y.at(index);
            };
            get_y(0) = Count_charged_hadrons_true(tau.lepton_gen_vis_pdg);
            get_y(1) = Count_neutral_hadrons_true(tau.lepton_gen_vis_pdg);

            //////////////////////////////////////////////////////////////////////
            // Sort inputs by decreasing pt:
            std::vector<size_t> indices(tau.pfCand_pt.size());
            std::iota(indices.begin(), indices.end(), 0);

            std::sort(indices.begin(), indices.end(), [&](size_t a, size_t b) {
                return tau.pfCand_pt.at(a) > tau.pfCand_pt.at(b);
            });
            //////////////////////////////////////////////////////////////////////


            for(size_t pf_ind = 0; pf_ind < indices.size(); ++pf_ind) {
                
                auto get_x = [&](Feature fe) -> float& {
                    size_t index = GetIndex_x(tau_ind, pf_ind, fe);
                    return data.x.at(index);
                };
                
                size_t pf_size = tau.pfCand_pt.size(); 
                static constexpr float def_val = 0.f;
                const bool has_cand = pf_ind < pf_size;
                size_t pf_ind_sorted = indices.at(pf_ind);

                const bool has_trk_details = has_cand && tau.pfCand_hasTrackDetails.at(pf_ind_sorted);
                const bool dz_not_NaN = has_cand && (std::isnormal(tau.pfCand_dz.at(pf_ind_sorted)) || tau.pfCand_dz.at(pf_ind_sorted) == 0);

                get_x(Feature::pfCand_pt)                   = has_cand ? tau.pfCand_pt.at(pf_ind_sorted)                   : def_val;
                get_x(Feature::pfCand_eta)                  = has_cand ? tau.pfCand_eta.at(pf_ind_sorted)                  : def_val;
                get_x(Feature::pfCand_phi)                  = has_cand ? tau.pfCand_phi.at(pf_ind_sorted)                  : def_val;
                get_x(Feature::pfCand_mass)                 = has_cand ? tau.pfCand_mass.at(pf_ind_sorted)                 : def_val;
                get_x(Feature::pfCand_pdgId)                = has_cand ? tau.pfCand_pdgId.at(pf_ind_sorted)                : def_val;
                get_x(Feature::pfCand_charge)               = has_cand ? tau.pfCand_charge.at(pf_ind_sorted)               : def_val;
                get_x(Feature::pfCand_pvAssociationQuality) = has_cand ? tau.pfCand_pvAssociationQuality.at(pf_ind_sorted) : def_val;
                get_x(Feature::pfCand_fromPV)               = has_cand ? tau.pfCand_fromPV.at(pf_ind_sorted)               : def_val;
                get_x(Feature::pfCand_puppiWeight)          = has_cand ? tau.pfCand_puppiWeight.at(pf_ind_sorted)          : def_val;
                get_x(Feature::pfCand_puppiWeightNoLep)     = has_cand ? tau.pfCand_puppiWeightNoLep.at(pf_ind_sorted)     : def_val;
                get_x(Feature::pfCand_lostInnerHits)        = has_cand ? tau.pfCand_lostInnerHits.at(pf_ind_sorted)        : def_val;
                get_x(Feature::pfCand_numberOfPixelHits)    = has_cand ? tau.pfCand_numberOfPixelHits.at(pf_ind_sorted)    : def_val;
                get_x(Feature::pfCand_numberOfHits)         = has_cand ? tau.pfCand_numberOfHits.at(pf_ind_sorted)         : def_val;
                get_x(Feature::pfCand_hasTrackDetails)      = has_cand ? tau.pfCand_hasTrackDetails.at(pf_ind_sorted)      : def_val;
                get_x(Feature::pfCand_dxy)                  = has_cand ? tau.pfCand_dxy.at(pf_ind_sorted)                  : def_val;
                get_x(Feature::pfCand_dz)                   = dz_not_NaN ? tau.pfCand_dz.at(pf_ind_sorted)                 : def_val;
                get_x(Feature::pfCand_caloFraction)         = has_cand ? tau.pfCand_caloFraction.at(pf_ind_sorted)         : def_val;
                get_x(Feature::pfCand_hcalFraction)         = has_cand ? tau.pfCand_hcalFraction.at(pf_ind_sorted)         : def_val;
                get_x(Feature::pfCand_rawCaloFraction)      = has_cand ? tau.pfCand_rawCaloFraction.at(pf_ind_sorted)      : def_val;
                get_x(Feature::pfCand_rawHcalFraction)      = has_cand ? tau.pfCand_rawHcalFraction.at(pf_ind_sorted)      : def_val;
                get_x(Feature::pfCand_valid)                = has_cand ? 1                                                 : 0      ;
                
                TLorentzVector *v = new TLorentzVector();
                v->SetPtEtaPhiM(tau.pfCand_pt.at(pf_ind_sorted), tau.pfCand_eta.at(pf_ind_sorted),tau.pfCand_phi.at(pf_ind_sorted),tau.pfCand_mass.at(pf_ind_sorted));
                get_x(Feature::pfCand_px)                   = has_cand ? v->Px() : def_val;
                get_x(Feature::pfCand_py)                   = has_cand ? v->Py() : def_val;
                get_x(Feature::pfCand_pz)                   = has_cand ? v->Pz() : def_val;
                get_x(Feature::pfCand_E)                    = has_cand ? v->E()  : def_val;

                get_x(Feature::pfCand_dxy_error)            = has_trk_details ? tau.pfCand_dxy_error.at(pf_ind_sorted)     : def_val;
                get_x(Feature::pfCand_dz_error)             = has_trk_details ? tau.pfCand_dz_error.at(pf_ind_sorted)      : def_val;
                get_x(Feature::pfCand_track_chi2)           = has_trk_details ? tau.pfCand_track_chi2.at(pf_ind_sorted)    : def_val;
                get_x(Feature::pfCand_track_ndof)           = has_trk_details ? tau.pfCand_track_ndof.at(pf_ind_sorted)    : def_val;
            }
            if(current_entry == end_dataset){
                tau_ind = n_tau;
            }
        }
        return data;
    }

    // Calculate the number of batches:
    size_t NumberOfBatches(){
        size_t n_entries = end_dataset-start_dataset;
        size_t n_batches = n_entries/n_tau;
        return n_batches;
    }

    // Resets the current entry to start_dataset so that we can loop on epochs:
    void Reset() {
        current_entry = start_dataset; 
    }

    // This function calculates the corresponding index in a 1D array: 
    // feed a = b.reshape(n_tau,n_pf,n_fe)
    size_t GetIndex_x(size_t _tau_ind, size_t _pf_ind, Feature _fe) const {
        size_t _fe_ind = static_cast<size_t>(_fe);
        size_t part_pf_direction  = n_fe*_pf_ind;
        size_t part_fe_direction  = _fe_ind;
        size_t part_tau_direction = n_fe*n_pf*_tau_ind;
        return part_fe_direction + part_pf_direction + part_tau_direction;
    }

    // This function calculates the corresponding index in a 1D array: 
    // feed a = b.reshape(n_tau,n_count)
    size_t GetIndex_y(size_t _tau_ind, size_t _count_ind) const {
        size_t part_count_direction = _count_ind;
        size_t part_tau_direction   = n_count*_tau_ind;
        return part_count_direction + part_tau_direction;
    }

    // Function that counts the true values for the number of charged hadrons for the event:
    size_t Count_charged_hadrons_true(std::vector<int> lepton_gen_vis_pdg){
        size_t cnt_charged_hadrons = 0;
        for(int pdg_id : lepton_gen_vis_pdg) {
            pdg_id = std::abs(pdg_id);
            if(pdg_id == 211 || pdg_id == 321) {
                ++cnt_charged_hadrons;
            }
        }
        return cnt_charged_hadrons;
    }

    // Function that counts the true values for the number of neutral hadrons for the event:
    size_t Count_neutral_hadrons_true(std::vector<int> lepton_gen_vis_pdg){
        size_t cnt_neutral_hadrons = 0;
        size_t cnt_photons = 0;
        for(int pdg_id : lepton_gen_vis_pdg) {
            pdg_id = std::abs(pdg_id);
            // 2 photons = 1 pi0:
            if(pdg_id == 22){
                ++cnt_photons;
                if(cnt_photons == 2){
                    ++cnt_neutral_hadrons;
                    cnt_photons = 0;
                }
            }else if(pdg_id == 310 || pdg_id == 130){
                ++cnt_neutral_hadrons;
            }
        }
        return cnt_neutral_hadrons;
    }

};