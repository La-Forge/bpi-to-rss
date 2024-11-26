import requests
from scrappers.BaseScrapper import BaseScrapper
import datetime 

FEED_PATH = 'feeds/idf_feed.xml'

class IleDeFranceScrapper(BaseScrapper):
    """
    Classe pour scrapper les données de l'Ile-de-France - appel à projets. 
    """
    def __init__(self):
        super().__init__(
            base_url="https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/aides-appels-a-projets/records",
            host="data.iledefrance.fr",
            feed_title="Aides et Appels à Projets - Île-de-France",
            feed_author="Île-de-France",
            feed_link="https://data.iledefrance.fr/explore/dataset/aides-appels-a-projets/",
        )
        self.limit_per_request = 100  
        self.has_pagination = False

    def scrapPages(self, verbose=False):
        """
        Récupère tous les enregistrements en gérant la limite de taille par requête
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
                print(f"Page avec offset {offset} : {len(current_records)} enregistrements récupérés.")

            if len(current_records) < self.limit_per_request:
                break

            offset += self.limit_per_request

        if verbose:
            print(f"Nombre total d'enregistrements récupérés : {len(all_records)}")

        return self.format_articles(all_records)

    def format_articles(self, data):
        """
        Formate les données API dans le format attendu par BaseScrapper.
        """
        articles = []
        for record in data:
            fields = record
            description_parts = [
            f"Description : {fields.get('chapo_txt', 'Pas de description disponible')}",
            f"Pour quel type de projet : {fields.get('objectif_txt', 'Non spécifié')}",
            f"Qui peut en bénéficier : {', '.join(fields.get('qui_peut_en_beneficier', [])) or 'Non spécifié'}"
            ]
            description = "\n".join(description_parts)
            articles.append({
                "title": fields.get("nom_de_l_aide_de_la_demarche", "Titre inconnu"),
                "link": fields.get("url_descriptif", ""),
                "description": description,
                "date": self.parse_date(fields.get("date")),
                "content_class": None, 
            })
        return articles

    @staticmethod
    def parse_date(date_str):
        """
        Transforme une date au format ISO 8601 en format RSS (RFC 822).
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            return None