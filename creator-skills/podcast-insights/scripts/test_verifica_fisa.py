"""Tests for the episode sheet validator. Run: python3 scripts/test_verifica_fisa.py"""
import unittest

from verifica_fisa import CATEGORII, verifica

DURATA = 50
TRANSCRIERE = "\n\n".join(f"[0:{m:02d}:00] text comun minutul {m}" for m in range(DURATA))
ANTET = "| Minut | Sursă | Ideea | Context | Pentru noi |\n|---|---|---|---|---|\n"
MINUTE = ["05:00", "15:00", "25:00", "35:00", "45:00", "01:00", "02:00", "03:00"]


def rand(minut="05:00", sursa="[SPUS]", ideea="Idee reformulată", context="Firmă mare", pentru_noi="acum: motiv clar"):
    return f"| {minut} | {sursa} | {ideea} | {context} | {pentru_noi} |\n"


def fisa(randuri=None, categorii=CATEGORII):
    """Build a valid sheet; `randuri` maps a category index to its replacement rows."""
    randuri = randuri or {}
    parti = ["# Fișă\n\n"]
    for i, categorie in enumerate(categorii):
        continut = randuri.get(i, rand(minut=MINUTE[i]))
        parti.append(f"## {categorie}\n\n{ANTET}{continut}\n")
    return "".join(parti)


class Verifica(unittest.TestCase):
    def erori(self, text, transcriere=TRANSCRIERE):
        return verifica(text, transcriere, DURATA)

    def assertRespinge(self, text, fragment, transcriere=TRANSCRIERE):
        erori = self.erori(text, transcriere)
        self.assertTrue(any(fragment in e for e in erori), f"lipsește {fragment!r} din {erori}")

    def test_fisa_minima_corecta_e_acceptata(self):
        self.assertEqual(self.erori(fisa()), [])

    def test_categorie_lipsa_e_respinsa(self):
        self.assertRespinge(fisa(categorii=CATEGORII[:-1]), "categorii")

    def test_categorii_in_ordine_gresita_sunt_respinse(self):
        inversate = [CATEGORII[1], CATEGORII[0]] + CATEGORII[2:]
        self.assertRespinge(fisa(categorii=inversate), "categorii")

    def test_rand_fara_cinci_coloane_e_respins(self):
        self.assertRespinge(fisa({0: "| 05:00 | [SPUS] | Idee |\n"}), "coloane")

    def test_minut_inexistent_in_transcriere_e_respins(self):
        self.assertRespinge(fisa({0: rand(minut="77:00")}), "minut")

    def test_minut_in_format_gresit_e_respins(self):
        self.assertRespinge(fisa({0: rand(minut="min 5")}), "minut")

    def test_sursa_necunoscuta_e_respinsa(self):
        self.assertRespinge(fisa({0: rand(sursa="[POATE]")}), "sursă")

    def test_neverificat_in_sursa_e_respins(self):
        self.assertRespinge(fisa({0: rand(sursa="[neverificat]")}), "sursă")

    def test_neverificat_in_celelalte_coloane_e_acceptat(self):
        text = fisa({0: rand(ideea="Idee [neverificat]", context="Cifră [neverificat]", pentru_noi="nu: motiv [neverificat]")})
        self.assertEqual(self.erori(text), [])

    def test_eticheta_pentru_noi_necunoscuta_e_respinsa(self):
        self.assertRespinge(fisa({0: rand(pentru_noi="poate: motiv")}), "Pentru noi")

    def test_motiv_gol_e_respins(self):
        self.assertRespinge(fisa({0: rand(pentru_noi="acum:")}), "Pentru noi")

    def test_mai_tarziu_e_acceptat(self):
        self.assertEqual(self.erori(fisa({0: rand(pentru_noi="mai târziu: după primii clienți")})), [])

    def test_varianta_cu_a_circumflex_e_respinsa_si_cu_majuscule(self):
        interzis = "S\u00c2NT"
        self.assertRespinge(fisa({0: rand(ideea=f"Noi {interzis} aici")}), "sunt")

    def test_doisprezece_cuvinte_copiate_sunt_respinse(self):
        copie = "unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece"
        transcriere = TRANSCRIERE + f"\n\n[0:49:00] {copie}"
        self.assertRespinge(fisa({0: rand(ideea=copie)}), "copiat", transcriere)

    def test_unsprezece_cuvinte_copiate_sunt_acceptate(self):
        copie = "unu doi trei patru cinci șase șapte opt nouă zece unsprezece"
        transcriere = TRANSCRIERE + f"\n\n[0:49:00] {copie} doisprezece"
        self.assertEqual(self.erori(fisa({0: rand(ideea=copie)}), transcriere), [])

    def test_copia_peste_limita_de_bloc_e_respinsa(self):
        transcriere = TRANSCRIERE + "\n\n[0:48:00] unu doi trei patru cinci șase\n\n[0:49:00] șapte opt nouă zece unsprezece doisprezece"
        ideea = "unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece"
        self.assertRespinge(fisa({0: rand(ideea=ideea)}), "copiat", transcriere)

    def test_copia_peste_marcaj_de_vorbitor_e_respinsa(self):
        transcriere = TRANSCRIERE + "\n\n[0:49:00] unu doi trei patru &gt;&gt; cinci șase șapte opt nouă zece unsprezece doisprezece"
        ideea = "unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece"
        self.assertRespinge(fisa({0: rand(ideea=ideea)}), "copiat", transcriere)

    def test_copia_peste_eticheta_e_respinsa(self):
        transcriere = TRANSCRIERE + "\n\n[0:49:00] unu doi trei patru [muzică] cinci șase șapte opt nouă zece unsprezece doisprezece"
        ideea = "unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece"
        self.assertRespinge(fisa({0: rand(ideea=ideea)}), "copiat", transcriere)

    def test_copia_fara_diacritice_e_respinsa(self):
        transcriere = TRANSCRIERE + "\n\n[0:49:00] unu doi trei patru cinci șase șapte opt nouă zece unsprezece doisprezece"
        ideea = "unu doi trei patru cinci sase sapte opt noua zece unsprezece doisprezece"
        self.assertRespinge(fisa({0: rand(ideea=ideea)}), "copiat", transcriere)

    def test_interval_de_zece_minute_fara_idee_e_respins(self):
        randuri = {i: rand(minut="05:00") for i in range(len(CATEGORII))}
        self.assertRespinge(fisa(randuri), "interval")

    def test_ideea_goala_e_respinsa(self):
        self.assertRespinge(fisa({0: rand(ideea="")}), "gol")

    def test_contextul_gol_e_respins(self):
        self.assertRespinge(fisa({0: rand(context="")}), "gol")

    def test_randul_indentat_e_verificat(self):
        self.assertRespinge(fisa({0: "  " + rand(minut="77:00")}), "minut")

    def test_interval_acoperit_doar_de_dedus_e_respins(self):
        randuri = {0: rand(minut="05:00", sursa="[DEDUS]"), 5: rand(minut="15:00"), 6: rand(minut="15:00"), 7: rand(minut="15:00")}
        self.assertRespinge(fisa(randuri), "interval 0")

    def test_interval_acoperit_doar_de_primele_minute_e_respins(self):
        randuri = {0: rand(minut="01:00"), 5: rand(minut="15:00"), 6: rand(minut="15:00"), 7: rand(minut="15:00")}
        self.assertRespinge(fisa(randuri), "interval 0")

    def test_categorie_fara_randuri_e_acceptata(self):
        self.assertEqual(self.erori(fisa({7: ""})), [])

    def test_minut_peste_60_gaseste_blocul_cu_ora(self):
        # yt-dlp/VTT stamps minute 62 as [1:02:00], not [0:62:00].
        lung = "\n\n".join(f"[{m // 60}:{m % 60:02d}:00] text comun minutul {m}" for m in range(70))
        randuri = {0: rand(minut="05:00"), 5: rand(minut="15:00") + rand(minut="25:00") + rand(minut="35:00")
                   + rand(minut="45:00") + rand(minut="55:00") + rand(minut="62:00")}
        self.assertEqual(verifica(fisa(randuri), lung, 70), [])


class CategoriiDinConfig(unittest.TestCase):
    def test_categorii_proprii_sunt_acceptate(self):
        proprii = ["Antrenament", "Nutriție", "Business", "Tooluri", "Mentalitate", "Clienți", "Conținut", "Resurse"]
        self.assertEqual(verifica(fisa(categorii=proprii), TRANSCRIERE, DURATA, proprii), [])

    def test_categoriile_implicite_resping_lista_proprie(self):
        proprii = ["Antrenament"] + CATEGORII[1:]
        self.assertTrue(verifica(fisa(categorii=proprii), TRANSCRIERE, DURATA))


if __name__ == "__main__":
    unittest.main()
