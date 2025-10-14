<?php
declare(strict_types=1);

namespace App\Model\Services;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use RuntimeException;

final class SerpClient
{
    public function __construct(
        private string $serpApiKey,
        private Client $http
    ) {}

    private function extractFirstApplyLinkFromJob(array $job): ?string
    {
        if (!empty($job['apply_options']) && is_array($job['apply_options'])) {
            foreach ($job['apply_options'] as $opt) {
                if (!empty($opt['link']) && is_string($opt['link'])) {
                    return $opt['link'];
                }
            }
        }
        return $job['share_link'] ?? null;
    }

    public function searchJobs(string $query, array $opts = []): array
    {
        $query = trim($query);
        if ($query === '') return [];

        unset($opts['engine'], $opts['job_id']);
        $params = array_merge([
            'engine'  => 'google_jobs',
            'q'       => $query,
            'hl'      => 'en',
            'api_key' => $this->serpApiKey,
        ], $opts);

        $json = $this->getJson('https://serpapi.com/search.json', $params);

        if (isset($json['error'])) {
            if (stripos($json['error'], "hasn't returned any results") !== false) return [];
            throw new \RuntimeException('SerpApi: ' . $json['error']);
        }

        $jobs = $json['jobs_results'] ?? [];
        foreach ($jobs as &$job) {
            $job['first_link'] = $this->extractFirstApplyLinkFromJob($job);
        }
        return $jobs;
    }

    public function resolveApplyLinks(string $jobId): array
    {
        $detail = $this->getJobDetails($jobId);

        $links = [];
        if (!empty($detail['apply_options']) && is_array($detail['apply_options'])) {
            foreach ($detail['apply_options'] as $opt) {
                if (!empty($opt['link'])) {
                    $links[] = [
                        'title' => $opt['title'] ?? 'Apply',
                        'link'  => $opt['link'],
                    ];
                }
            }
        }
        if (!$links && !empty($detail['apply_link'])) {
            $links[] = ['title' => 'Apply', 'link' => $detail['apply_link']];
        }
        if (!$links && !empty($detail['share_link'])) {
            $links[] = ['title' => 'Open in Google Jobs', 'link' => $detail['share_link']];
        }
        return $links;
    }

    public function getJobDetails(string $jobId, array $opts = []): array
    {
        if ($jobId === '') {
            throw new \InvalidArgumentException('jobId is empty for google_jobs_listing');
        }

        unset($opts['engine']); 
        $params = array_merge([
            'engine'  => 'google_jobs_listing',
            'job_id'  => $jobId,
            'hl'      => 'en',
            'api_key' => $this->serpApiKey,
        ], $opts);

        $json = $this->getJson('https://serpapi.com/search.json', $params);

        if (isset($json['error'])) {
            \Tracy\Debugger::barDump($params, 'SerpApi params (listing)');
            \Tracy\Debugger::barDump($json, 'SerpApi response (listing)');
            throw new \RuntimeException('SerpApi: ' . $json['error']);
        }
        return $json;
    }

    /**
     * Вспомогательный запрос с обработкой сетевых ошибок
     */
    private function getJson(string $url, array $query): array
    {
        try {
            $resp = $this->http->get($url, [
                'query'   => $query,
                'timeout' => 15,
                'headers' => [
                    'Accept' => 'application/json',
                ],
            ]);
        } catch (GuzzleException $e) {
            throw new RuntimeException('HTTP error: ' . $e->getMessage(), 0, $e);
        }

        $body = (string) $resp->getBody();
        $data = json_decode($body, true);

        if (!is_array($data)) {
            throw new RuntimeException('Invalid JSON from SerpApi: ' . substr($body, 0, 500));
        }
        return $data;
        }
}