<?php

namespace App\Model\Services;


use Nette;
use Nette\Database\Context;
use Nette\Database\Explorer;

class OffersService
{
    private Context $db;
    private string $rootDir;

    public function __construct(
        string $rootDir,
        Context $db, 
    )
    {
        $this->rootDir = $rootDir;
        $this->db = $db;
    }

    public function processOffersRewrite(): void
    {
        $path_profesia = $this->rootDir . '/.docker/embedding/server/soup/job_parsed.json';
        if (!is_file($path_profesia)) {
            throw new \RuntimeException("Файл не найден: $path_profesia");
        }
    
        $data = json_decode((string)file_get_contents($path_profesia), true, 512, JSON_THROW_ON_ERROR);
    
        // Нормализуем вход: объект → массив из одного элемента
        $items = isset($data[0]) ? $data : [$data];
    
        $count = 0;
        foreach ($items as $it) {
            if (!is_array($it)) continue;
    
            $row = [
                'title'    => trim((string)($it['title']    ?? '')),
                'company'  => trim((string)($it['company']  ?? '')),
                'location' => trim((string)($it['location'] ?? '')),
                'salary'   => trim((string)($it['salary']   ?? '')),
                'url'      => trim((string)($it['url']      ?? '')),
            ];
    
            // Минимальный фильтр: должно быть хотя бы что-то осмысленное
            if ($row['title'] === '' && $row['url'] === '') continue;
    
            $this->db->table('offer')->insert($row);
            $count++;
        }
    
        echo "Inserted: {$count}\n";
    }

    public function processOffersPraceZaRohemRewrite()
    {
        $path_prace_za_rohem = $this->rootDir . '/.docker/embedding/server/pracezarohem/pracezarohem.json';
        if (!is_file($path_prace_za_rohem)) {
            throw new \RuntimeException("Файл не найден: $path_prace_za_rohem");
        }

        $data_prace_za_rohem = json_decode((string)file_get_contents($path_prace_za_rohem), true, 512, JSON_THROW_ON_ERROR);

        $items_prace_za_rohem = isset($data_prace_za_rohem[0]) ? $data_prace_za_rohem : [$data_prace_za_rohem];

        $count = 0;
        foreach ($items_prace_za_rohem as $it) {
            if (!is_array($it)) continue;
    
            $row = [
                'title'    => trim((string)($it['title']    ?? '')),
                'address'  => trim((string)($it['address']  ?? '')),
                'far_away' => trim((string)($it['far_away'] ?? '')),
                'job_condition'   => trim((string)($it['job_condition']   ?? '')),
            ];
    
            // Минимальный фильтр: должно быть хотя бы что-то осмысленное
            if ($row['title'] === '' && $row['address'] === '' && $row['far_away'] && $row['job_condition']) continue;
    
            $this->db->table('offer_prace_za_rohem')->insert($row);
            $count++;
        }
        echo "Inserted: {$count}\n";
    }

    public function processOffersJockstackitRewrite(){
        $path = $this->rootDir . '/.docker/embedding/server/jobstackit/jobstackit.json';
        if (!is_file($path)) {
            throw new \RuntimeException("Файл не найден: $path");
        }

        $data = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);

        $item = isset($data[0]) ? $data: [$data];

        $count = 0;
        foreach ($item as $it) {
            if (!is_array($it)) continue;
    
            $row = [
                'title'    => trim((string)($it['title']    ?? '')),
                'list'  => trim((string)($it['list']  ?? '')),
                'level'  => trim((string)($it['level']  ?? '')),
                'firma' => trim((string)($it['firma'] ?? '')),
                'address'   => trim((string)($it['address']   ?? '')),
                'salary'   => trim((string)($it['salary']   ?? '')),
            ];
    
            // Минимальный фильтр: должно быть хотя бы что-то осмысленное
            if ($row['title'] === '' && $row['list'] === '' && $row['level'] === '' && $row['firma'] && $row['address'] && $row['salary']) continue;
    
            $this->db->table('offer_jobstackit')->insert($row);
            $count++;
        }
        echo "Inserted: {$count}\n";
    }
      
}