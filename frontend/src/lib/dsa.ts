/**
 * Frontend Data Structures & Algorithms (DSA) Engine for Thai EduCenter:
 * 1. ClientLRUCache: True O(1) LRU Cache for search query results & API responses.
 *
 * (DSA audit 2026-09-10: removed the unused ClientTrie and its doc entries —
 * zero imports anywhere; "FastRanker" was never implemented, docs drift.)
 */

import type { Course, FacultyMember, ResearchLab, SearchMatchResult } from "@/types";

class LRUNode<K, V> {
  key: K;
  val: V;
  prev: LRUNode<K, V> | null = null;
  next: LRUNode<K, V> | null = null;

  constructor(key: K, val: V) {
    this.key = key;
    this.val = val;
  }
}

export class ClientLRUCache<K, V> {
  private capacity: number;
  private map: Map<K, LRUNode<K, V>> = new Map();
  private head: LRUNode<K, V>;
  private tail: LRUNode<K, V>;

  constructor(capacity: number = 64) {
    this.capacity = capacity;
    this.head = new LRUNode<K, V>(undefined as K, undefined as V);
    this.tail = new LRUNode<K, V>(undefined as K, undefined as V);
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  private remove(node: LRUNode<K, V>): void {
    const prev = node.prev;
    const next = node.next;
    if (prev) prev.next = next;
    if (next) next.prev = prev;
  }

  private addToHead(node: LRUNode<K, V>): void {
    node.next = this.head.next;
    node.prev = this.head;
    if (this.head.next) {
      this.head.next.prev = node;
    }
    this.head.next = node;
  }

  get(key: K): V | undefined {
    const node = this.map.get(key);
    if (!node) return undefined;

    this.remove(node);
    this.addToHead(node);
    return node.val;
  }

  put(key: K, val: V): void {
    if (this.map.has(key)) {
      const node = this.map.get(key)!;
      node.val = val;
      this.remove(node);
      this.addToHead(node);
      return;
    }

    if (this.map.size >= this.capacity) {
      const lru = this.tail.prev;
      if (lru && lru !== this.head) {
        this.remove(lru);
        this.map.delete(lru.key);
      }
    }

    const newNode = new LRUNode(key, val);
    this.map.set(key, newNode);
    this.addToHead(newNode);
  }

  has(key: K): boolean {
    return this.map.has(key);
  }

  clear(): void {
    this.map.clear();
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  get size(): number {
    return this.map.size;
  }
}

// Global client caches
export type SearchCacheValue = Course[] | SearchMatchResult[] | ResearchLab[];

export const searchApiCache = new ClientLRUCache<string, SearchCacheValue>(64);
export const facultyDetailCache = new ClientLRUCache<string, FacultyMember>(128);
export const courseDetailCache = new ClientLRUCache<string, Course>(128);
export const labDetailCache = new ClientLRUCache<string, ResearchLab>(64);
