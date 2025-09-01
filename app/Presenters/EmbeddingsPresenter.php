<?php

declare(strict_types=1);

namespace App\Presenters;

use Nette;
use Nette\Application\UI\Form;
use Nette\Database\Context;
use Nette\Application\UI\Presenter;
use App\Model\ACLForm;
use App\Model\Services\EmbeddingsService;

class EmbeddingsPresenter extends Presenter 
{
    /** @var EmbeddingsService @inject */
    public $embeddingsService;

    /** @var Context @inject */
    public $db;

    // Kontrola všech poli
    public function actionControl($text, $predefined)
    {
        $queryEmbedding = $this->embeddingsService->get_embedding([$text])[0];
        $results = [];

        if ($predefined === 'contacts') {
            $rows = $this->db->query("SELECT * FROM article_branche")->fetchAll();
            foreach ($rows as $row) {
                $results[] = [
                    'type' => 'contacts',
                    'article_id' => $row['article_id'],
                    'similarity' => null,
                    'name_branche' => $row['name'],
                    'content_branche' => $row['content'],
                    'homepage_name' => $row['homepage_name'],
                ];
            }
            $this->sendJson(['result' => $results]);
            return;
        }
    
        if ($predefined === 'works') {
            $rows = $this->db->query("SELECT * FROM article_new WHERE name LIKE ?", 'Job Offer%')->fetchAll();
            foreach ($rows as $row) {
                $results[] = [
                    'type' => 'works',
                    'article_id' => $row['article_id'],
                    'similarity' => null,
                    'name_new' => $row['name'],
                    'perex_new' => $row['perex'],
                    'content_new' => $row['content'],
                    'place_new' => $row['place'],
                ];
            }
            $this->sendJson(['result' => $results]);
            return;
        }
    
        $queryEmbedding = $this->embeddingsService->get_embedding([$text])[0];
    
        if ($predefined === 'works') {
            $allProductEmbeddings = $this->embeddingsService->getAllProductsEmbeddings();
            foreach ($allProductEmbeddings as $item) {
                $data = json_decode($item->union_date, true);
                $maxSimilarity = 0;
    
                foreach (['code', 'name', 'description', 'short_description'] as $field) {
                    if (empty($data[$field]) || count($queryEmbedding) !== count($data[$field])) continue;
                    $similarity = $this->embeddingsService->cosine_similarity($queryEmbedding, $data[$field]);
                    if ($similarity > $maxSimilarity) $maxSimilarity = $similarity;
                }
                if ($maxSimilarity > 0) {
                    $product_category_language = $this->db->query(
                        "SELECT * FROM product_language WHERE product_id = ?",
                        $item['product_id']
                    )->fetch();

                    $product_in_eshop_order = $this->db->query(
                        "SELECT * FROM product_in_eshop_order WHERE product_id = ?",
                        $item['product_id']
                    )->fetch();

                    $main_image = $this->db->query(
                        "SELECT * FROM product_image WHERE product_id = ? AND is_main = 1 LIMIT 1",
                        $item['product_id']
                    )->fetch();
                    $img_path = $main_image ? $main_image['path'] : null;
    
                    $results[] = [
                        'type' => 'product',
                        'product_id' => $item['product_id'],
                        'similarity' => $maxSimilarity,
                        'name' => $product_category_language['name'] ?? null,
                        'description' => $product_category_language['description'] ?? null,
                        'short_description' => $product_category_language['short_description'] ?? null,
                        'selling_price' => $product_in_eshop_order['selling_price'] ?? null,
                        'url' => $product_category_language['url'] ?? null,
                        'path' => $img_path
                    ];
                }
            }
        } 
        // elseif ($predefined === 'contacts') 
        // {
        //     $allArticleEmbeddings = $this->embeddingsService->getAllArticleEmbeddings();
        //     foreach ($allArticleEmbeddings as $article_item) {
        //         $data = json_decode($article_item->union_date, true);
        //         $maxSimilarity = 0;
        //         foreach (['type', 'name', 'content'] as $field) {
        //             if (empty($data[$field]) || count($queryEmbedding) !== count($data[$field])) continue;
        //             $similarity = $this->embeddingsService->cosine_similarity($queryEmbedding, $data[$field]);
        //             if ($similarity > $maxSimilarity) $maxSimilarity = $similarity;
        //         }
        //         if ($maxSimilarity > 0) {
        //             $article_branche = $this->db->query(
        //                 "SELECT * FROM article_branche WHERE article_id = ?",
        //                 $article_item['article_id']
        //             )->fetch();

        //             $results[] = [
        //                 'type' => 'contacts',
        //                 'article_id' => $article_item['article_id'],
        //                 'similarity' => $maxSimilarity,
        //                 'name_branche' => $article_branche['name'] ?? null,
        //                 'content_branche' => $article_branche['content'] ?? null,
        //                 'homepage_name' => $article_branche['homepage_name'] ?? null,
        //             ];
        //         }
        //     }
        // } 
        // elseif ($predefined === 'works') 
        // {
        //     $allArticleEmbeddings = $this->embeddingsService->getAllArticleEmbeddings();
        //     foreach ($allArticleEmbeddings as $article_item) {
        //         $data = json_decode($article_item->union_date, true);
        //         $maxSimilarity = 0;
        //         foreach (['type', 'name', 'content'] as $field) {
        //             if (empty($data[$field]) || count($queryEmbedding) !== count($data[$field])) continue;
        //             $similarity = $this->embeddingsService->cosine_similarity($queryEmbedding, $data[$field]);
        //             if ($similarity > $maxSimilarity) $maxSimilarity = $similarity;
        //         }
        //         if ($maxSimilarity > 0) {
        //             $article_new = $this->db->query(
        //                 "SELECT * FROM article_new WHERE article_id = ? AND name LIKE ?",
        //                 $article_item['article_id'],
        //                 'Job Offer%'
        //             )->fetch();

        //             $results[] = [
        //                 'type' => 'works',
        //                 'article_id' => $article_item['article_id'],
        //                 'similarity' => $maxSimilarity,
        //                 'name_new' => $article_new['name'] ?? null,
        //                 'perex_new' => $article_new['perex'] ?? null,
        //                 'content_new' => $article_new['content'] ?? null,
        //                 'place_new' => $article_new['place'] ?? null,
        //             ];
        //         }
        //     }
        // } 
        else {
            file_put_contents(__DIR__.'/debug.txt', "No branch. predefined: " . print_r($predefined, true));
        }
    
        usort($results, fn($a, $b) => $b['similarity'] <=> $a['similarity']);
        $this->sendJson(['result' => array_slice($results, 0, 5)]);
    }    

}
