<?php

namespace App\Model\Services;

use Nette;
use Nette\Database\Context;
use Nette\Database\Explorer;


class EmbeddingsService 
{
    private Context $db;

    public function __construct(Context $db)
    {
        $this->db = $db;
    }
    
    public function get_embedding($texts)
    {
        $url = 'http://localhost:5005/embed';

        $data = json_encode(['texts' => $texts]);

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json'
        ]);
        $result = curl_exec($ch); 
        curl_close($ch);
        return json_decode($result, true)['embeddings'] ?? [];
    }

    private function getProductEmbeddings(){
        $products = $this->db->query("SELECT * FROM product")->fetchAll();
        $embeddings = [];

        foreach($products as $product){
            $embeddings[$product->id] = [
            'name' => $this->get_embedding($product->name),
            'description' => $this->get_embedding($product->description),
            ];
        }
        return $embeddings;
    }

    public function processProducts()
    {
        $products = $this->db->query("SELECT * FROM product")->fetchAll();
        $getProductsEmbeddings = $this->getProductEmbeddings();
        foreach($products as $product){
            $product_id = $product->id;

            $data = array_merge(
                $getProductsEmbeddings[$product_id] ?? [],
            );
            $json = json_encode($data); 
            
            $this->db->query(
                "INSERT INTO embedding (product_id, union_date) VALUES (?, ?)",
                $product_id, $json
            );
        }
    }
    

    private function getArticleEmbeddings(){
        $articles = $this->db->query("SELECT * FROM article")->fetchAll();
        $embeddings = [];

        foreach($articles as $article){
            $embeddings[$article->id] = [
            'type' => $this->get_embedding($article->type),
            ];
        }
        return $embeddings;
    }


    public function processArticles()
    {
        $articles = $this->db->query("SELECT * FROM article")->fetchAll();
        $getArticlesEmbeddings = $this->getArticleEmbeddings();
        foreach($articles as $article){
            $article_id = $article->id;

            $data = array_merge(
                $getArticlesEmbeddings[$article_id] ?? [],
            );
            $json = json_encode($data); 
            
            $this->db->query(
                "INSERT INTO embedding_article (article_id, union_date) VALUES (?, ?)",
                $article_id, $json
            );
        }
    }

        // Dá se doplnit další tabulky

    public function getAllProductsEmbeddings()
    {
        return $this->db->query("SELECT product_id, union_date FROM embedding")->fetchAll();
    }

    public function getAllArticleEmbeddings()
    {
        return $this->db->query("SELECT article_id, union_date FROM embedding_article")->fetchAll();
    }

    // public function getAllContactsEmbeddings()
    // {
    //     return $this->db->query("SELECT contact_id, union_date FROM embedding_contact")->fetchAll();
    // }

    public function cosine_similarity($a, $b) {
        $dot = 0.0;
        $normA = 0.0;
        $normB = 0.0;
        for ($i = 0; $i < count($a); $i++) {
            $dot += $a[$i] * $b[$i];
            $normA += $a[$i] ** 2;
            $normB += $b[$i] ** 2;
        }
        return $dot / (sqrt($normA) * sqrt($normB));
    }

    public function findMostSimilarProducts($query, $limit = 5)
    {
        $queryEmbedding = $this->get_embedding([$query])[0];
        $allEmbeddings = $this->getAllProductsEmbeddings();

        $results = [];
        $weights = [
            'name' => 0.5,
            'description' => 0.5,
        ];

        foreach ($allEmbeddings as $item) {
            $embeddingFields = json_decode($item['union_date'], true);
            if (!is_array($embeddingFields)) continue;

            $weightedSum = 0;
            $weightTotal = 0;

            foreach ($weights as $field => $weight) {
                if (!empty($embeddingFields[$field]) && is_array($embeddingFields[$field])) {
                    $sim = $this->cosine_similarity($queryEmbedding, $embeddingFields[$field]);
                    $weightedSum += $sim * $weight;
                    $weightTotal += $weight;
                }
            }
            $finalScore = $weightTotal > 0 ? $weightedSum / $weightTotal : 0;

            $results[] = [
                'product_id' => $item['product_id'],
                'similarity' => $finalScore,
            ];
        }
        usort($results, fn($a, $b) => $b['similarity'] <=> $a['similarity']);
        return array_slice($results, 0, $limit);
    }
}