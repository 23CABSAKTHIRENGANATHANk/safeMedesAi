import { useMutation } from "@tanstack/react-query";
import { verifyMedicine, VerifyPayload } from "../services/api";

export function useVerifyMedicine() {
  return useMutation({
    mutationFn: (payload: VerifyPayload) => verifyMedicine(payload),
  });
}
