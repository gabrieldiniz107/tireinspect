from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from service_orders.models import ServiceOrder, ServiceOrderTruck


class Command(BaseCommand):
    help = (
        "Atribui numeração sequencial GLOBAL aos caminhões dos pedidos, "
        "em ordem cronológica (por padrão: order_date, depois created_at e IDs), "
        "independentemente do usuário ou da empresa."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reassign-all",
            action="store_true",
            help="Reatribui números para todos os caminhões (cuidado: pode mudar números já atribuídos)",
        )
        parser.add_argument(
            "--by",
            choices=["order_date", "created_at"],
            default="order_date",
            help="Campo base para ordenação cronológica (padrão: order_date)",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Apenas mostra o que seria alterado"
        )

    def handle(self, *args, **opts):
        by = opts["by"]
        reassign_all = opts["reassign_all"]
        dry = opts["dry_run"]

        # Garante created_by preenchido para todos os trucks
        q_missing_user = ServiceOrderTruck.objects.filter(created_by__isnull=True).select_related("order")
        if q_missing_user.exists():
            self.stdout.write(f"Preenchendo created_by em {q_missing_user.count()} caminhões…")
            for t in q_missing_user:
                t.created_by_id = t.order.created_by_id if t.order_id else None
                if not dry:
                    t.save(update_fields=["created_by"])

        # Base queryset: TODOS os trucks (global)
        trucks_qs = ServiceOrderTruck.objects.select_related("order")
        if not reassign_all:
            trucks_qs = trucks_qs.filter(truck_number__isnull=True)

        # Ordenação estável global
        if by == "order_date":
            trucks_qs = trucks_qs.order_by(
                "order__order_date",
                "order__created_at",
                "created_at",
                "id",
            )
        else:  # created_at
            trucks_qs = trucks_qs.order_by(
                "order__created_at",
                "created_at",
                "id",
            )

        trucks = list(trucks_qs)
        if not trucks:
            self.stdout.write("Nenhum caminhão a numerar.")
            return

        # Descobrir início da sequência GLOBAL
        start = 3000
        if not reassign_all:
            last = (
                ServiceOrderTruck.objects
                .filter(truck_number__isnull=False)
                .aggregate(m=Max("truck_number"))
                .get("m")
            )
            if last is not None:
                start = last + 1

        curr = start
        self.stdout.write(f"Atribuindo números globalmente a {len(trucks)} caminhões a partir de {curr}…")
        total_updated = 0
        with transaction.atomic():
            # Se for reatribuir todos, primeiro zera para evitar conflitos na UNIQUE existente
            if reassign_all and not dry:
                for t in trucks:
                    if t.truck_number is not None:
                        t.truck_number = None
                        t.save(update_fields=["truck_number"])

            for t in trucks:
                if reassign_all or t.truck_number is None:
                    if not dry:
                        t.truck_number = curr
                        # mantém created_by coerente com a ordem, se faltar
                        if t.created_by_id is None and t.order_id:
                            t.created_by_id = t.order.created_by_id
                        t.save(update_fields=["truck_number", "created_by"])
                    self.stdout.write(f"  - Truck id={t.id} -> Nº {curr} (pedido={t.order_id})")
                    curr += 1
                    total_updated += 1

        self.stdout.write(self.style.SUCCESS(f"Concluído. Caminhões atualizados: {total_updated}"))
