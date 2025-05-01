import networkx as nx
from pyvis.network import Network
from SPARQLWrapper import SPARQLWrapper, JSON

class WikiDataChatBot:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entity_id = ""
        self.entity_label = ""

    def fetch_wikidata_triples(self, entity_id):
        """Fetch subject-predicate-object triples for a Wikidata entity using SPARQL."""
        # Clean up the entity ID format
        entity_id = entity_id.strip().upper()
        if not entity_id.startswith('Q'):
            entity_id = 'Q' + entity_id
        
        self.entity_id = entity_id
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

        query = f"""
        SELECT ?predicateLabel ?objectLabel ?entityLabel WHERE {{
          wd:{entity_id} ?predicate ?object .
          FILTER(STRSTARTS(STR(?predicate), STR(wdt:)))
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
          wd:{entity_id} rdfs:label ?entityLabel .
          FILTER(LANG(?entityLabel) = "en")
        }}
        LIMIT 100
        """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        
        try:
            results = sparql.query().convert()
        except Exception as e:
            print(f"❌ Error querying Wikidata: {e}")
            return [], ""

        triples = []
        entity_label = ""

        if "results" in results and "bindings" in results["results"]:
            for result in results["results"]["bindings"]:
                pred = result["predicateLabel"]["value"]
                obj = result["objectLabel"]["value"]
                label = result["entityLabel"]["value"]
                entity_label = label  # will be same for all
                triples.append((label, pred, obj))

        if entity_label:
            print(f"✅ Fetched {len(triples)} triples for {entity_label}")
        else:
            print(f"❌ No data found for entity {entity_id}")
            
        return triples, entity_label

    def build_knowledge_graph(self, triples):
        """Build the graph from triples"""
        for subj, pred, obj in triples:
            self.graph.add_node(subj)
            self.graph.add_node(obj)
            self.graph.add_edge(subj, obj, label=pred)

        print(f"✅ Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")

    def visualize_graph(self, graph, output_filename="graph.html", entity_label="Entity"):
        net = Network(height="700px", width="100%", bgcolor="#222222", font_color="white", notebook=False)
        net.force_atlas_2based()

        for node in graph.nodes:
            net.add_node(node, label=node)

        for source, target, data in graph.edges(data=True):
            net.add_edge(source, target, title=data['label'], label=data['label'])

        # Save and open manually
        net.write_html(output_filename)
        print(f"✅ Visualization saved as {output_filename}. Open it in your browser.")
        
    def train_on_triples(self, triples):
        self.knowledge = {}
        for subj, pred, obj in triples:
            pred = pred.lower()
            if pred not in self.knowledge:
                self.knowledge[pred] = []
            self.knowledge[pred].append(obj)

    def answer_question(self, question):
        question = question.lower().strip()
        
        # Handle basic questions about the entity itself
        if question == self.entity_label.lower() or question == f"what is {self.entity_label.lower()}" or question == f"who is {self.entity_label.lower()}":
            basic_info = []
            key_predicates = ["instance of", "subclass of", "part of", "nature of", "description"]
            for pred in key_predicates:
                if pred in self.knowledge:
                    basic_info.extend([f"{pred.title()}: {val}" for val in self.knowledge[pred]])
            if basic_info:
                return "\n".join(basic_info)

        # Mapping user intent to likely Wikidata predicates - generalized for any entity type
        intent_map = {
            "what": ["instance of", "subclass of", "part of", "nature of", "description"],
            "who": ["instance of", "occupation", "field of work", "creator", "manufacturer", "developer"],
            "where": ["location", "coordinate location", "country", "continent", "located in", "headquarters location"],
            "when": ["inception", "date of birth", "date of death", "point in time", "start time", "end time"],
            "how": ["mass", "height", "length", "width", "depth", "quantity", "duration"],
            "description": ["description", "definition", "nature of"],
            "type": ["instance of", "subclass of", "nature of"],
            "part": ["part of", "has part", "contains"],
            "use": ["use", "function", "purpose", "application"],
            "made": ["manufacturer", "creator", "inventor", "developer", "founded by", "inception"],
            "material": ["material used", "made from", "consists of"],
            "size": ["mass", "height", "length", "width", "depth", "area", "volume"],
            "location": ["location", "coordinate location", "country", "continent"],
            "origin": ["country of origin", "place of origin", "inception", "discovered by"],
            "related": ["related to", "similar to", "opposite of", "derivative work"],
            "property": ["color", "shape", "material", "style", "genre", "classification"]
        }

        # Find matching intents
        matched_preds = set()
        for key, predicates in intent_map.items():
            if key in question:
                matched_preds.update(predicates)

        if not matched_preds:
            return ("❌ I couldn't understand the question. Try asking about:\n"
                   "- What it is (type, classification)\n"
                   "- Where it's located\n"
                   "- When it was created/discovered\n"
                   "- How it's used or what it's made of\n"
                   "- Its properties (size, color, etc.)\n"
                   "- Who created or discovered it\n"
                   "- What it's related to")

        # Search for matching predicates and collect answers
        answers = []
        for pred in matched_preds:
            pred_lower = pred.lower()
            if pred_lower in self.knowledge:
                values = self.knowledge[pred_lower]
                for val in values:
                    answers.append(f"{pred.title()}: {val}")

        if not answers:
            return f"❌ I know about {self.entity_label}, but I don't have information about that specific aspect."

        return "\n".join(answers)

    def run(self):
        entity_id = input("Enter Wikidata Entity ID (e.g., Q937 for Einstein): ").strip()
        triples, entity_label = self.fetch_wikidata_triples(entity_id)
        self.entity_label = entity_label  # Store entity_label as instance variable
        
        if not triples:
            print("❌ No triples found for this entity. Please try another entity ID.")
            return
            
        self.train_on_triples(triples)
        self.build_knowledge_graph(triples)

        self.visualize_graph(self.graph, entity_label=entity_label)

        print(f"💬 You can now ask questions about {entity_label}!")
        while True:
            question = input("You: ")
            if question.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            response = self.answer_question(question)
            print("Bot:", response)

if __name__ == "__main__":
    bot = WikiDataChatBot()
    bot.run()
