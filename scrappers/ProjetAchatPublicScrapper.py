import requests
from scrappers.APIScrapper import APIScrapper
import dateparser
from datetime import timezone

FEED_PATH = 'feeds/projetachat_feed.xml'

class ProjetsAchatScrapper(APIScrapper):
    """
    Scrapper pour l'API 'Projets d'achats publics' (APProch).
    Source: https://data.economie.gouv.fr/explore/dataset/projets-dachats-publics/
    """
    def __init__(self):
        super().__init__(
            base_url="https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/projets-dachats-publics/records",
            host="data.economie.gouv.fr",
            feed_title="Projets d’achats publics – APProch",
            feed_author="Ministère de l’Économie, des Finances et de l’Industrie",
            feed_link="https://data.economie.gouv.fr/explore/dataset/projets-dachats-publics/",
        )
        self.limit_per_request = 100
        self._siren_cache = {}
    def get_entity_name_from_siren(self, siren):
        """
        Retourne le nom de l'entité (dénomination) à partir d'un SIREN
        via l'API Recherche d'entreprises (social.gouv).
        Docs: https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/
        """
        if not siren:
            return None
        s = str(siren).strip()
        # Le SIREN est sur 9 chiffres; si ce n'est pas le cas, on essaie quand même mais on gère prudemment.
        if s in self._siren_cache:
            return self._siren_cache[s]

        url = f"https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/entreprise/{s}"
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                js = resp.json() or {}
                # Champs possibles selon l'API
                name = (
                    js.get("nom_complet")
                    or js.get("label")
                    or js.get("nom_raison_sociale")
                    or js.get("nom")
                )
                self._siren_cache[s] = name
            else:
                self._siren_cache[s] = None
        except requests.RequestException:
            self._siren_cache[s] = None

        return self._siren_cache[s]

    def scrapPages(self, verbose=False):
        """
        Récupère tous les enregistrements en gérant la pagination (limit/offset).
        """
        all_records = []
        offset = 0

        while True:
            params = {
                "limit": self.limit_per_request,
                "offset": offset,
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            current_records = data.get("results", [])
            all_records.extend(current_records)

            if verbose:
                print(f"Total cumulé après offset {offset}: {len(all_records)}")

            if verbose:
                print(f"Page offset={offset} : {len(current_records)} enregistrements")

            if len(current_records) < self.limit_per_request:
                break

            offset += self.limit_per_request

        if verbose:
            print(f"Total récupéré : {len(all_records)}")

        return self.format_articles(all_records)

    def format_articles(self, data):
        """
        Formate les données API dans le format attendu 
        """
        articles = []

        for rec in data:
            fields = rec.get('fields', rec)
            siren = fields.get('siren_de_l_entite_acheteuse')
            entite_nom = self.get_entity_name_from_siren(siren)

            description_parts = [
                f"Description : {fields.get('description', '—')}",
                f"Statut : {fields.get('statut', 'Pas de statut défini')}",
                f"Catégorie d'achat : {fields.get('categorie_d_achat', 'Pas de catégorie d\'achat définie')}",
                f"Date prévisionnelle de publication : {fields.get('date_previsionnelle_de_publication', 'Pas de date prévisionnelle de publication définie')}",
                f"Entité acheteuse : {entite_nom or '—'} (SIREN : {siren or '—'})",
                f"Montant estimé du marché : {fields.get('montant_estime_du_marche', 'Pas de montant estimé du marché défini')}",
                f"Durée prévisionnelle du marché : {fields.get('duree_previsionnelle_du_marche')} mois" if fields.get('duree_previsionnelle_du_marche') else "Durée prévisionnelle du marché : Pas de durée prévisionnelle du marché définie",
            ]
            description = "\n".join(description_parts)

            code = fields.get('code')
            link = f"https://projets-achats.marches-publics.gouv.fr/project/{code}" if code else "https://projets-achats.marches-publics.gouv.fr/"

            # Try multiple date fields; APIScrapper/BaseScrapper often skips items without a date
            date_candidates = [
                fields.get('date_previsionnelle_de_publication'),
                fields.get('date_de_publication'),
                fields.get('date_mise_en_ligne'),
                fields.get('date'),
                fields.get('updated_at'),
                fields.get('created_at'),
            ]
            date_value = next((d for d in date_candidates if d), None)

            articles.append({
                'title': fields.get('libelle', 'Pas de titre'),
                'link': link,
                'description': description,
                'date': self.parse_date(date_value),
                'content_class': None,
            })

        return articles

    @staticmethod
    def parse_date(date_str):
        """
        Convertit une date texte en objet datetime *aware* (UTC) pour Feedgen.
        Si la date n'a pas d'information de fuseau, on force UTC.
        """
        if not date_str:
            return None
        dt = dateparser.parse(str(date_str))
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt