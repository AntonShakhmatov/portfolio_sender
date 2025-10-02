<?php

namespace App\Presenters;

use Nette;
use Nette\Application\Responses\JsonResponse;
use Nette\Application\Responses\TextResponse;
use App\Model\Services\ApiTalksStoreService;

final class TestPresenter extends Nette\Application\UI\Presenter
{
    public function __construct(private ApiTalksStoreService $api) {}

    public function renderShow(): void
    {
        $data = $this->api->getVolnaPracovniMista();

        $this->template->status = 200;
        $this->template->error  = null;
        $this->template->raw    = json_encode($data);
        $this->template->data   = $data;
        $this->template->jsonPretty = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    }
}